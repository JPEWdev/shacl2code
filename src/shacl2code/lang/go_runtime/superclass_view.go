package runtime

import (
	"fmt"
	"reflect"
)

// SuperclassView is a helper function to emulate some semblance of inheritance,
// while still having simple structs without embedding, it is highly experimental
func SuperclassView[View any](base any) *View {
	var view *View
	baseValue := reflect.ValueOf(base)
	baseType := baseValue.Type()
	validateBaseType(baseType) // base must be a pointer, see usage examples
	viewType := reflect.TypeOf(view)
	validateFieldAlignment(baseType, viewType) // base memory layout must be compatible with view
	view = reflect.NewAt(viewType.Elem(), baseValue.UnsafePointer()).Interface().(*View)
	return view
}

func validateBaseType(base reflect.Type) {
	if base.Kind() != reflect.Pointer {
		panic(fmt.Errorf("invalid base type; must be a pointer"))
	}
	if base.Elem().Kind() != reflect.Struct {
		panic(fmt.Errorf("invalid base type; must be a pointer to a struct"))
	}
}

func validateFieldAlignment(base, view reflect.Type) {
	// should be passed either 2 pointers to struct types or 2 struct types
	if base.Kind() == reflect.Pointer && view.Kind() == reflect.Pointer {
		base = base.Elem()
		view = view.Elem()
	}
	if base.Kind() != reflect.Struct || view.Kind() != reflect.Struct {
		panic(fmt.Errorf("base and view types must point to structs; got base: %s and view: %s", typeName(base), typeName(view)))
	}
	// view needs to be a subset of the number of fields in base
	if view.NumField() > base.NumField() {
		panic(fmt.Errorf("view %s (%d fields) is not a subset of %s (%d fields)", typeName(view), view.NumField(), typeName(base), base.NumField()))
	}
	for i := 0; i < view.NumField(); i++ {
		baseField := base.Field(i)
		viewField := view.Field(i)
		// ignore zero-sized fields
		if baseField.Type.Size() == 0 && viewField.Type.Size() == 0 {
			continue
		}
		// field layout must be identical, name _should_ be the same
		if baseField.Name != viewField.Name {
			panic(fmt.Errorf("field %d in base is named %s but view expects %s", i, baseField.Name, viewField.Name))
		}
		if baseField.Type != viewField.Type {
			panic(fmt.Errorf("field %d in base is has type %s but view expects %s", i, typeName(baseField.Type), typeName(viewField.Type)))
		}
		if baseField.Offset != viewField.Offset {
			panic(fmt.Errorf("field %d in base is named %d but view expects %d", i, baseField.Offset, viewField.Offset))
		}
		// seems to align
	}
}
