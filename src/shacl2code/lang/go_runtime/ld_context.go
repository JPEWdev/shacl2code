package runtime

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"path"
	"reflect"
	"strings"
)

// ldType is a 0-size data holder property type for type-level linked data
type ldType struct{}

// ldContext is the holder for all known LD contexts and required definitions
type ldContext map[string]*serializationContext

// RegisterTypes registers types to be used when serializing/deserialising documents
func (c ldContext) RegisterTypes(contextUrl string, types ...any) ldContext {
	ctx := c[contextUrl]
	if ctx == nil {
		ctx = &serializationContext{
			contextUrl:    contextUrl,
			typeAlias:     "type", // FIXME this needs to come from the LD context
			iriToType:     map[string]*typeContext{},
			typeToContext: map[reflect.Type]*typeContext{},
		}
		c[contextUrl] = ctx
	}
	for _, typ := range types {
		ctx.registerType(typ)
	}
	return c
}

// IRIMap registers compact IRIs for the given type
func (c ldContext) IRIMap(contextUrl string, typ any, nameMap map[string]string) ldContext {
	c.RegisterTypes(contextUrl) // ensure there is a context created
	ctx := c[contextUrl]

	t := reflect.TypeOf(typ)
	t = baseType(t) // types should be passed as pointers; we want the base types
	tc := ctx.typeToContext[t]
	if tc == nil {
		ctx.registerType(typ)
		tc = ctx.typeToContext[t]
	}
	for iri, compact := range nameMap {
		tc.iriToName[iri] = compact
		tc.nameToIri[compact] = iri
	}
	return c
}

func (c ldContext) ToJSON(writer io.Writer, value any) error {
	vals, err := c.toMaps(value)
	if err != nil {
		return err
	}
	enc := json.NewEncoder(writer)
	enc.SetEscapeHTML(false)
	return enc.Encode(vals)
}

func (c ldContext) toMaps(o ...any) (values map[string]any, errors error) {
	// the ld graph is referenced here
	// traverse the go objects to output to the graph
	builder := graphBuilder{
		ldc:   c,
		input: o,
		ids:   map[reflect.Value]string{},
	}

	var err error
	var context *serializationContext
	for _, o := range builder.input {
		context, err = builder.add(o)
		if err != nil {
			return nil, err
		}
	}

	return map[string]any{
		ldContextProp: context.contextUrl,
		ldGraphProp:   builder.toGraph(),
	}, nil
}

func (c ldContext) FromJSON(reader io.Reader) ([]any, error) {
	vals := map[string]any{}
	dec := json.NewDecoder(reader)
	err := dec.Decode(&vals)
	if err != nil {
		return nil, err
	}
	return c.FromMaps(vals)
}

func (c ldContext) FromMaps(values map[string]any) ([]any, error) {
	instances := map[string]reflect.Value{}

	var errs error
	var graph []any

	context, _ := values[ldContextProp].(string)
	currentContext := c[context]
	if currentContext == nil {
		return nil, fmt.Errorf("unknown document %s type: %v", ldContextProp, context)
	}

	nodes, _ := values[ldGraphProp].([]any)
	if nodes == nil {
		return nil, fmt.Errorf("%s array not present in root object", ldGraphProp)
	}

	// one pass to create all the instances
	for _, node := range nodes {
		_, err := c.getOrCreateInstance(currentContext, instances, anyType, node)
		errs = appendErr(errs, err)
	}

	// second pass to fill in all refs
	for _, node := range nodes {
		got, err := c.getOrCreateInstance(currentContext, instances, anyType, node)
		errs = appendErr(errs, err)
		if err == nil && got.IsValid() {
			graph = append(graph, got.Interface())
		}
	}

	return graph, errs
}

func (c ldContext) getOrCreateInstance(currentContext *serializationContext, instances map[string]reflect.Value, expectedType reflect.Type, incoming any) (reflect.Value, error) {
	if isPrimitive(expectedType) {
		if convertedVal := convertTo(incoming, expectedType); convertedVal != emptyValue {
			return convertedVal, nil
		}
		return emptyValue, fmt.Errorf("unable to convert incoming value to type %v: %+v", typeName(expectedType), incoming)
	}
	switch incoming := incoming.(type) {
	case string:
		instance := c.findById(currentContext, instances, incoming)
		if instance != emptyValue {
			return instance, nil
		}
		// not found: have a complex type with string indicates an IRI or other primitive
		switch expectedType.Kind() {
		case reflect.Pointer:
			expectedType = expectedType.Elem()
			if isPrimitive(expectedType) {
				val, err := c.getOrCreateInstance(currentContext, instances, expectedType, incoming)
				if err != nil {
					return emptyValue, err
				}
				instance = reflect.New(expectedType)
				instance.Elem().Set(val)
				return instance, nil
			}
			if expectedType.Kind() == reflect.Struct {
				return emptyValue, fmt.Errorf("unexpected pointer reference external IRI reference: %v", incoming)
			}
			fallthrough
		case reflect.Struct:
			instance = reflect.New(expectedType)
			instance = instance.Elem()
			err := c.setStructProps(currentContext, instances, instance, map[string]any{
				ldIDProp: incoming,
			})
			return instance, err
		case reflect.Interface:
			// an IRI with an interface is a reference to an unknown type, so use the closest type
			newType, found := c.findExternalReferenceType(currentContext, expectedType)
			if found {
				instance = reflect.New(newType)
				// try to return the appropriately assignable instance
				if !instance.Type().AssignableTo(expectedType) {
					instance = instance.Elem()
				}
				err := c.setStructProps(currentContext, instances, instance, map[string]any{
					ldIDProp: incoming,
				})
				return instance, err
			}
			return emptyValue, fmt.Errorf("unable to determine external reference type while populating %v for IRI reference: %v", typeName(expectedType), incoming)
		default:
		}
	case map[string]any:
		return c.getOrCreateFromMap(currentContext, instances, incoming)
	}
	return emptyValue, fmt.Errorf("unexpected data type: %#v", incoming)
}

func convertTo(incoming any, typ reflect.Type) reflect.Value {
	v := reflect.ValueOf(incoming)
	if v.CanConvert(typ) {
		return v.Convert(typ)
	}
	return emptyValue
}

func (c ldContext) findById(_ *serializationContext, instances map[string]reflect.Value, incoming string) reflect.Value {
	inst, ok := instances[incoming]
	if ok {
		return inst
	}
	return emptyValue
}

func (c ldContext) getOrCreateFromMap(currentContext *serializationContext, instances map[string]reflect.Value, incoming map[string]any) (reflect.Value, error) {
	typ, ok := incoming[ldTypeProp].(string)
	if !ok && currentContext.typeAlias != "" {
		typ, ok = incoming[currentContext.typeAlias].(string)
	}
	if !ok {
		return emptyValue, fmt.Errorf("not a string")
	}

	t, ok := currentContext.iriToType[typ]
	if !ok {
		return emptyValue, fmt.Errorf("don't have type: %v", typ)
	}

	id, _ := incoming[ldIDProp].(string)
	if id == "" && t.idProp != "" {
		id, _ = incoming[t.idProp].(string)
	}
	inst, ok := instances[id]
	if !ok {
		inst = reflect.New(baseType(t.typ)) // New(T) returns *T
		if id != "" {
			// only set instance references when an ID is provided
			instances[id] = inst
		}
	}

	// valid type, make a new one and fill it from the incoming maps
	return inst, c.fill(currentContext, instances, inst, incoming)
}

func (c ldContext) fill(currentContext *serializationContext, instances map[string]reflect.Value, instance reflect.Value, incoming any) error {
	switch incoming := incoming.(type) {
	case string:
		inst := c.findById(currentContext, instances, incoming)
		if inst != emptyValue {
			return c.setValue(currentContext, instances, instance, inst)
		}
		// should be an incoming ID if string
		return c.setValue(currentContext, instances, instance, map[string]any{
			ldIDProp: incoming,
		})
	case map[string]any:
		return c.setStructProps(currentContext, instances, instance, incoming)
	}
	return fmt.Errorf("unsupported incoming data type: %#v attempting to set instance: %#v", incoming, instance.Interface())
}

func (c ldContext) setValue(currentContext *serializationContext, instances map[string]reflect.Value, target reflect.Value, incoming any) error {
	var errs error
	typ := target.Type()
	switch typ.Kind() {
	case reflect.Slice:
		switch incoming := incoming.(type) {
		case []any:
			return c.setSliceValue(currentContext, instances, target, incoming)
		}
		// try mapping a single value to an incoming slice
		return c.setValue(currentContext, instances, target, []any{incoming})
	case reflect.Struct:
		switch incoming := incoming.(type) {
		case map[string]any:
			return c.setStructProps(currentContext, instances, target, incoming)
		case string:
			// named individuals just need an object with the iri set
			return c.setStructProps(currentContext, instances, target, map[string]any{
				ldIDProp: incoming,
			})
		}
	case reflect.Interface, reflect.Pointer:
		switch incoming := incoming.(type) {
		case string, map[string]any:
			inst, err := c.getOrCreateInstance(currentContext, instances, typ, incoming)
			errs = appendErr(errs, err)
			if inst != emptyValue {
				target.Set(inst)
				return nil
			}
		}
	default:
		if newVal := convertTo(incoming, typ); newVal != emptyValue {
			target.Set(newVal)
		} else {
			errs = appendErr(errs, fmt.Errorf("unable to convert %#v to %s, dropping", incoming, typeName(typ)))
		}
	}
	return nil
}

func (c ldContext) setStructProps(currentContext *serializationContext, instances map[string]reflect.Value, instance reflect.Value, incoming map[string]any) error {
	var errs error
	typ := instance.Type()
	for typ.Kind() == reflect.Pointer {
		instance = instance.Elem()
		typ = instance.Type()
	}
	if typ.Kind() != reflect.Struct {
		return fmt.Errorf("unable to set struct properties on non-struct type: %#v", instance.Interface())
	}
	tc := currentContext.typeToContext[typ]
	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)
		if skipField(field) {
			continue
		}
		fieldVal := instance.Field(i)

		propIRI := field.Tag.Get(propIriTag)
		if propIRI == "" {
			continue
		}
		incomingVal, ok := incoming[propIRI]
		if !ok {
			compactIRI := field.Tag.Get(propIriCompactTag)
			if compactIRI != "" {
				incomingVal, ok = incoming[compactIRI]
			}
		}
		if !ok {
			continue
		}
		// don't set blank node IDs, these will be regenerated on output
		if propIRI == ldIDProp {
			if tc != nil {
				if str, ok := incomingVal.(string); ok {
					if fullIRI, ok := tc.nameToIri[str]; ok {
						incomingVal = fullIRI
					}
				}
			}
			if isBlankNodeID(incomingVal) {
				continue
			}
		}
		errs = appendErr(errs, c.setValue(currentContext, instances, fieldVal, incomingVal))
	}
	return errs
}

func (c ldContext) setSliceValue(currentContext *serializationContext, instances map[string]reflect.Value, target reflect.Value, incoming []any) error {
	var errs error
	sliceType := target.Type()
	if sliceType.Kind() != reflect.Slice {
		return fmt.Errorf("expected slice, got: %#v", target)
	}
	sz := len(incoming)
	if sz > 0 {
		elemType := sliceType.Elem()
		newSlice := reflect.MakeSlice(sliceType, 0, sz)
		for i := 0; i < sz; i++ {
			incomingValue := incoming[i]
			if incomingValue == nil {
				continue // don't allow null values
			}
			newItemValue, err := c.getOrCreateInstance(currentContext, instances, elemType, incomingValue)
			errs = appendErr(errs, err)
			if newItemValue != emptyValue {
				// validate we can actually set the type
				if newItemValue.Type().AssignableTo(elemType) {
					newSlice = reflect.Append(newSlice, newItemValue)
				}
			}
		}
		target.Set(newSlice)
	}
	return errs
}

func (c ldContext) findExternalReferenceType(currentContext *serializationContext, expectedType reflect.Type) (reflect.Type, bool) {
	tc := currentContext.typeToContext[expectedType]
	if tc != nil {
		return tc.typ, true
	}
	bestMatch := anyType
	for t := range currentContext.typeToContext {
		if t.Kind() != reflect.Struct {
			continue
		}
		// the type with the fewest fields assignable to the target is a good candidate to be an abstract type
		if reflect.PointerTo(t).AssignableTo(expectedType) && (bestMatch == anyType || bestMatch.NumField() > t.NumField()) {
			bestMatch = t
		}
	}
	if bestMatch != anyType {
		currentContext.typeToContext[expectedType] = &typeContext{
			typ: bestMatch,
		}
		return bestMatch, true
	}
	return anyType, false
}

func skipField(field reflect.StructField) bool {
	return field.Type.Size() == 0
}

func typeName(t reflect.Type) string {
	switch {
	case isPointer(t):
		return "*" + typeName(t.Elem())
	case isSlice(t):
		return "[]" + typeName(t.Elem())
	case isMap(t):
		return "map[" + typeName(t.Key()) + "]" + typeName(t.Elem())
	case isPrimitive(t):
		return t.Name()
	}
	return path.Base(t.PkgPath()) + "." + t.Name()
}

func isSlice(t reflect.Type) bool {
	return t.Kind() == reflect.Slice
}

func isMap(t reflect.Type) bool {
	return t.Kind() == reflect.Map
}

func isPointer(t reflect.Type) bool {
	return t.Kind() == reflect.Pointer
}

func isPrimitive(t reflect.Type) bool {
	switch t.Kind() {
	case reflect.String,
		reflect.Int,
		reflect.Int8,
		reflect.Int16,
		reflect.Int32,
		reflect.Int64,
		reflect.Uint,
		reflect.Uint8,
		reflect.Uint16,
		reflect.Uint32,
		reflect.Uint64,
		reflect.Float32,
		reflect.Float64,
		reflect.Bool:
		return true
	default:
		return false
	}
}

const (
	ldIDProp          = "@id"
	ldTypeProp        = "@type"
	ldContextProp     = "@context"
	ldGraphProp       = "@graph"
	typeIriTag        = "iri"
	typeIriCompactTag = "iri-compact"
	propIriTag        = "iri"
	propIriCompactTag = "iri-compact"
	typeIdPropTag     = "id-prop"
	propIsRequiredTag = "required"
)

var (
	emptyValue reflect.Value
	anyType    = reflect.TypeOf((*any)(nil)).Elem()
)

type typeContext struct {
	typ       reflect.Type
	iri       string
	compact   string
	idProp    string
	iriToName map[string]string
	nameToIri map[string]string
}

type serializationContext struct {
	contextUrl    string
	typeAlias     string
	iriToType     map[string]*typeContext
	typeToContext map[reflect.Type]*typeContext
}

func fieldByType[T any](t reflect.Type) (reflect.StructField, bool) {
	var v T
	typ := reflect.TypeOf(v)
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		if f.Type == typ {
			return f, true
		}
	}
	return reflect.StructField{}, false
}

func (m *serializationContext) registerType(instancePointer any) {
	t := reflect.TypeOf(instancePointer)
	t = baseType(t) // types should be passed as pointers; we want the base types

	tc := m.typeToContext[t]
	if tc != nil {
		return // already registered
	}
	tc = &typeContext{
		typ:       t,
		iriToName: map[string]string{},
		nameToIri: map[string]string{},
	}
	meta, ok := fieldByType[ldType](t)
	if ok {
		tc.iri = meta.Tag.Get(typeIriTag)
		tc.compact = meta.Tag.Get(typeIriCompactTag)
		tc.idProp = meta.Tag.Get(typeIdPropTag)
	}
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		if !isIdField(f) {
			continue
		}
		compactIdProp := f.Tag.Get(typeIriCompactTag)
		if compactIdProp != "" {
			tc.idProp = compactIdProp
		}
	}
	m.iriToType[tc.iri] = tc
	m.iriToType[tc.compact] = tc
	m.typeToContext[t] = tc
}

// appendErr appends errors, flattening joined errors
func appendErr(err error, errs ...error) error {
	if joined, ok := err.(interface{ Unwrap() []error }); ok {
		return errors.Join(append(joined.Unwrap(), errs...)...)
	}
	if err == nil {
		return errors.Join(errs...)
	}
	return errors.Join(append([]error{err}, errs...)...)
}

// baseType returns the base type if this is a pointer or interface
func baseType(t reflect.Type) reflect.Type {
	switch t.Kind() {
	case reflect.Pointer, reflect.Interface:
		return baseType(t.Elem())
	default:
		return t
	}
}

// isBlankNodeID indicates this is a blank node ID, e.g. _:CreationInfo-1
func isBlankNodeID(val any) bool {
	if val, ok := val.(string); ok {
		return strings.HasPrefix(val, "_:")
	}
	return false
}
