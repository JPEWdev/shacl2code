//
//
//

package model

import (
    "encoding/json"
    "fmt"
    "reflect"
    "regexp"
    "sort"
    "strconv"
    "strings"
    "time"

    "github.com/ncruces/go-strftime"
)

// Validation Error
type ValidationError struct {
    Property string
    Err string
}

func (e *ValidationError) Error() string { return e.Property + ": " + e.Err }

// Conversion Error
type ConversionError struct {
    From string
    To string
}

func (e *ConversionError) Error() string {
    return "Unable to convert from " + e.From + " to " + e.To
}

// Decode Error
type DecodeError struct {
    Path Path
    Err string
}

func (e *DecodeError) Error() string {
    return e.Path.ToString() + ": " + e.Err
}

// Path
type Path struct {
    Path []string
}

func (p *Path) PushPath(s string) Path {
    new_p := *p
    new_p.Path = append(new_p.Path, s)
    return new_p
}

func (p *Path) PushIndex(idx int) Path {
    return p.PushPath("[" + strconv.Itoa(idx) + "]")
}

func (p *Path) ToString() string {
    return "." + strings.Join(p.Path, ".")
}

// Error Handler
type ErrorHandler interface {
    HandleError(error, Path)
}

// Reference
type Ref[T SHACLObject] interface {
    GetIRI() string
    GetObj() T
    IsSet() bool
    IsObj() bool
    IsIRI() bool
}

type ref[T SHACLObject] struct {
    obj *T
    iri string
}

func (r ref[T]) GetIRI() string {
    if r.iri != "" {
        return r.iri
    }
    if r.obj != nil {
        o := *r.obj
        if o.ID().IsSet() {
            return o.ID().Get()
        }
    }
    return ""
}

func (r ref[T]) GetObj() T {
    return *r.obj
}

func (r ref[T]) IsSet() bool { return r.IsIRI() || r.IsObj() }
func (r ref[T]) IsObj() bool { return r.obj != nil }
func (r ref[T]) IsIRI() bool { return r.iri != "" }

func MakeObjectRef[T SHACLObject](obj T) Ref[T] {
    return ref[T]{&obj, ""}
}

func MakeIRIRef[T SHACLObject](iri string) Ref[T] {
    return ref[T]{nil, iri}
}

// Convert one reference to another. Note that the output type is first so it
// can be specified, while the input type is generally inferred from the argument
func ConvertRef[TO SHACLObject, FROM SHACLObject](in Ref[FROM]) (Ref[TO], error) {
    if in.IsObj() {
        out_obj, ok := any(in.GetObj()).(TO)
        if !ok {
            return nil, &ConversionError{reflect.TypeOf(ref[FROM]{}).Name(), reflect.TypeOf(ref[TO]{}).Name()}
        }
        return ref[TO]{&out_obj, in.GetIRI()}, nil
    }
    return ref[TO]{nil, in.GetIRI()}, nil
}

type Visit func(Path, any)

// Base SHACL Object
type SHACLObjectBase struct {
    // Object ID
    id Property[string]
    typ SHACLType
    typeIRI string
}

func (self *SHACLObjectBase) ID() PropertyInterface[string] { return &self.id }

func (self *SHACLObjectBase) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true

    switch self.typ.GetNodeKind() {
    case NodeKindBlankNode:
        if self.ID().IsSet() && ! IsBlankNode(self.ID().Get()) {
            handler.HandleError(&ValidationError{
                "id",
                "ID must by be blank node"},
                path.PushPath("id"))
            valid = false
        }
    case NodeKindIRI:
        if ! self.ID().IsSet() || ! IsIRI(self.ID().Get()) {
            handler.HandleError(&ValidationError{
                "id",
                "ID must be an IRI"},
                path.PushPath("id"))
            valid = false
        }
    case NodeKindBlankNodeOrIRI:
        if self.ID().IsSet() && ! IsBlankNode(self.ID().Get()) && ! IsIRI(self.ID().Get()) {
            handler.HandleError(&ValidationError{
                "id",
                "ID must be a blank node or IRI"},
                path.PushPath("id"))
            valid = false
        }
    default:
        panic("Unknown node kind")
    }

    return valid
}

func (self *SHACLObjectBase) Walk(path Path, visit Visit) {
    self.id.Walk(path, visit)
}

func (self *SHACLObjectBase) EncodeProperties(data map[string]interface{}, path Path) error {
    if self.typeIRI != "" {
        data["@type"] = self.typeIRI
    } else {
        data["@type"] = self.typ.GetCompactTypeIRI().GetDefault(self.typ.GetTypeIRI())
    }

    if self.id.IsSet() {
        id_prop := self.typ.GetIDAlias().GetDefault("@id")
        data[id_prop] = EncodeIRI(self.id.Get(), path.PushPath(id_prop), map[string]string{})
    }

    return nil
}

func (self *SHACLObjectBase) GetType() SHACLType {
    return self.typ
}

func (self *SHACLObjectBase) setType(typ SHACLType) {
    self.typ = typ
}

func (self *SHACLObjectBase) setTypeIRI(iri string) {
    self.typeIRI = iri
}

func ConstructSHACLObjectBase(o *SHACLObjectBase) *SHACLObjectBase {
    o.id = NewProperty[string]("id", []Validator[string]{ IDValidator{}, })
    return o
}

type SHACLObject interface {
    ID() PropertyInterface[string]
    Validate(path Path, handler ErrorHandler) bool
    Walk(path Path, visit Visit)
    EncodeProperties(data map[string]interface{}, path Path) error
    GetType() SHACLType
    setType(typ SHACLType)
    setTypeIRI(iri string)
}

// Extensible Object

type SHACLExtensibleBase struct {
    properties map[string][]any
}

func (self *SHACLExtensibleBase) GetExtProperty(name string) []any {
    return self.properties[name]
}

func (self *SHACLExtensibleBase) SetExtProperty(name string, value []any) {
    if self.properties == nil {
        self.properties = make(map[string][]any)
    }
    self.properties[name] = value
}

func (self *SHACLExtensibleBase) DeleteExtProperty(name string) {
    delete(self.properties, name)
}

func (self *SHACLExtensibleBase) EncodeExtProperties(data map[string]any, path Path) error {
    for k, values := range self.properties {
        if len(values) == 0 {
            continue
        }

        lst := []any{}
        for _, v := range values {
            lst = append(lst, v)
        }
        data[k] = lst
    }
    return nil
}

type SHACLExtensibleObject interface {
    GetExtProperty(string) []any
    SetExtProperty(string, []any)
    DeleteExtProperty(string)
}

// Type Metadata
const NodeKindBlankNode = 0
const NodeKindIRI = 1
const NodeKindBlankNodeOrIRI = 2

type SHACLType interface {
    GetTypeIRI() string
    GetCompactTypeIRI() Optional[string]
    GetNodeKind() int
    GetIDAlias() Optional[string]
    DecodeProperty(SHACLObject, string, interface{}, Path) (bool, error)
    Create() SHACLObject
    IsAbstract() bool
    IsExtensible() bool
    IsSubClassOf(SHACLType) bool
}

type SHACLTypeBase struct {
    typeIRI string
    compactTypeIRI Optional[string]
    idAlias Optional[string]
    isExtensible Optional[bool]
    isAbstract bool
    parentIRIs []string
    nodeKind Optional[int]
}

func (self SHACLTypeBase) GetTypeIRI() string {
    return self.typeIRI
}

func (self SHACLTypeBase) GetCompactTypeIRI() Optional[string] {
    return self.compactTypeIRI
}

func (self SHACLTypeBase) GetNodeKind() int {
    if self.nodeKind.IsSet() {
        return self.nodeKind.Get()
    }

    for _, parent_id := range(self.parentIRIs) {
        p := objectTypes[parent_id]
        return p.GetNodeKind()
    }

    return NodeKindBlankNodeOrIRI
}

func (self SHACLTypeBase) GetIDAlias() Optional[string] {
    if self.idAlias.IsSet() {
        return self.idAlias
    }

    for _, parent_id := range(self.parentIRIs) {
        p := objectTypes[parent_id]
        a := p.GetIDAlias()
        if a.IsSet() {
            return a
        }
    }

    return self.idAlias
}

func (self SHACLTypeBase) IsAbstract() bool {
    return self.isAbstract
}

func (self SHACLTypeBase) IsExtensible() bool {
    if self.isExtensible.IsSet() {
        return self.isExtensible.Get()
    }

    for _, parent_id := range(self.parentIRIs) {
        p := objectTypes[parent_id]
        if p.IsExtensible() {
            return true
        }
    }

    return false
}

func (self SHACLTypeBase) IsSubClassOf(other SHACLType) bool {
    if other.GetTypeIRI() == self.typeIRI {
        return true
    }

    for _, parent_id := range(self.parentIRIs) {
        p := objectTypes[parent_id]
        if p.IsSubClassOf(other) {
            return true
        }
    }

    return false
}

func (self SHACLTypeBase) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    id_alias := self.GetIDAlias()
    if id_alias.IsSet() {
        switch name {
        case id_alias.Get():
            val, err := DecodeString(value, path.PushPath(name), map[string]string{})
            if err != nil {
                return false, err
            }
            err = o.ID().Set(val)
            if err != nil {
                return false, err
            }
            return true, nil
        case "@id":
            return true, &DecodeError{
                path.PushPath(name),
                "'@id' is not allowed for " + self.GetTypeIRI() + " which has an ID alias",
            }
        }
    } else if name == "@id" {
        val, err := DecodeString(value, path.PushPath(name), map[string]string{})
        if err != nil {
            return false, err
        }
        err = o.ID().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    }

    for _, parent_id := range(self.parentIRIs) {
        p := objectTypes[parent_id]
        found, err := p.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    if self.isExtensible.GetDefault(false) {
        obj := o.(SHACLExtensibleObject)
        v, err := DecodeAny(value, path, map[string]string{})
        if err != nil {
            return false, err
        }

        lst, is_list := v.([]interface{})
        if is_list {
            obj.SetExtProperty(name, lst)
        } else {
            obj.SetExtProperty(name, []interface{}{v})
        }
        return true, nil
    }
    return false, nil
}


var objectTypes map[string] SHACLType

func RegisterType(typ SHACLType) {
    objectTypes[typ.GetTypeIRI()] = typ
    compact := typ.GetCompactTypeIRI()
    if compact.IsSet() {
        objectTypes[compact.Get()] = typ
    }
}

// SHACLObjectSet
type SHACLObjectSet interface {
    AddObject(r SHACLObject)
    Decode(decoder *json.Decoder) error
    Encode(encoder *json.Encoder) error
    Walk(visit Visit)
    Validate(handler ErrorHandler) bool
}

type SHACLObjectSetObject struct {
    objects []SHACLObject
}

func (self *SHACLObjectSetObject) AddObject(r SHACLObject) {
    self.objects = append(self.objects, r)
}

func (self *SHACLObjectSetObject) Decode(decoder *json.Decoder) error {
    path := Path{}

    var data map[string]interface{}
    if err := decoder.Decode(&data); err != nil {
        return err
    }

    {
        v, ok := data["@context"]
        if ! ok {
            return &DecodeError{path, "@context missing"}
        }

        sub_path := path.PushPath("@context")
        value, ok := v.(string)
        if ! ok {
            return &DecodeError{sub_path, "@context must be a string, or list of string"}
        }
        if value != "https://spdx.github.io/spdx-3-model/context.json" {
            return &DecodeError{sub_path, "Wrong context URL '" + value + "'"}
        }
    }

    delete(data, "@context")

    decodeProxy := func (data any, path Path, context map[string]string) (SHACLObject, error) {
        return DecodeSHACLObject[SHACLObject](data, path, context, nil)
    }

    _, has_graph := data["@graph"]
    if has_graph {
        for k, v := range data {
            switch k {
            case "@graph": {
                objs, err := DecodeList[SHACLObject](
                    v,
                    path.PushPath("@graph"),
                    map[string]string{},
                    decodeProxy,
                )

                if err != nil {
                    return err
                }

                for _, obj := range objs {
                    self.AddObject(obj)
                }
            }

            default:
                return &DecodeError{path, "Unknown property '" + k + "'"}
            }
        }
    } else {
        obj, err := decodeProxy(data, path, map[string]string{})
        if err != nil {
            return err
        }

        self.AddObject(obj)
    }

    return nil
}

func (self *SHACLObjectSetObject) Encode(encoder *json.Encoder) error {
    data := make(map[string]interface{})
    data["@context"] = "https://spdx.github.io/spdx-3-model/context.json"
    path := Path{}

    if len(self.objects) == 1 {
        err := self.objects[0].EncodeProperties(data, path)
        if err != nil {
            return err
        }
    } else if len(self.objects) > 1 {
        graph_path := path.PushPath("@graph")
        lst := []interface{}{}
        for idx, o := range self.objects {
            d := make(map[string]interface{})
            err := o.EncodeProperties(d, graph_path.PushIndex(idx))
            if err != nil {
                return err
            }
            lst = append(lst, d)
        }

        data["@graph"] = lst
    }

    return encoder.Encode(data)
}

func (self *SHACLObjectSetObject) Walk(visit Visit) {
    path := Path{}
    visited := map[SHACLObject]bool{}

    visit_proxy := func (path Path, v any) {
        switch v.(type) {
        case Ref[SHACLObject]:
            r := v.(Ref[SHACLObject])
            if ! r.IsObj() {
                visit(path, v)
                return
            }

            o := r.GetObj()
            _, ok := visited[o]
            if ok {
                return
            }
            visited[o] = true
            visit(path, v)
            o.Walk(path, visit)
            return

        default:
            visit(path, v)
            return
        }
    }

    for idx, o := range(self.objects) {
        sub_path := path.PushIndex(idx)
        visit_proxy(sub_path, MakeObjectRef(o))
    }
}

func (self *SHACLObjectSetObject) Validate(handler ErrorHandler) bool {
    valid := true

    visit_proxy := func (path Path, v any) {
        r, ok := v.(Ref[SHACLObject])
        if ! ok {
            return
        }

        if ! r.IsObj() {
            return
        }

        if ! r.GetObj().Validate(path, handler) {
            valid = false
        }
    }

    self.Walk(visit_proxy)

    return valid
}

func NewSHACLObjectSet() SHACLObjectSet {
    os := SHACLObjectSetObject{}
    return &os
}

func DecodeAny(data any, path Path, context map[string]string) (any, error) {
    switch data.(type) {
    case map[string]interface{}:
        return DecodeRef[SHACLObject](data, path, context, nil)
    case string:
        return DecodeString(data, path, context)
    case int:
        return DecodeInteger(data, path, context)
    case float64:
        return DecodeFloat(data, path, context)
    case bool:
        return DecodeBoolean(data, path, context)
    case []interface{}:
        return DecodeList[any](data, path, context, DecodeAny)
    default:
        return nil, &DecodeError{path, "Unknown type "+ reflect.TypeOf(data).Name()}
    }
}

func DecodeSHACLObject[T SHACLObject](data any, path Path, context map[string]string, targetType SHACLType) (T, error) {
    dict, ok := data.(map[string]interface{})
    if ! ok {
        return *new(T), &DecodeError{path, "Expected dictionary or string. Got " + reflect.TypeOf(data).Name()}
    }

    var v interface{}
    v, ok = dict["@type"]
    if ! ok {
        v, ok = dict["@type"]
        if ! ok {
            return *new(T), &DecodeError{path, "type missing"}
        }
    }

    var type_iri string
    var create_type SHACLType

    type_iri, ok = v.(string)
    if ! ok {
        return *new(T), &DecodeError{path, "Wrong type for @type. Got " + reflect.TypeOf(v).Name()}
    }

    iri_typ, ok := objectTypes[type_iri]
    if ok {
        if targetType != nil && !iri_typ.IsSubClassOf(targetType) {
            return *new(T), &DecodeError{path, "Type " + type_iri + " is not valid where " +
                    targetType.GetTypeIRI() + " is expected"}
        }

        if iri_typ.IsAbstract() {
            return *new(T), &DecodeError{path, "Unable to create abstract type '" + type_iri + "'"}
        }

        create_type = iri_typ
    } else if targetType != nil && targetType.IsExtensible() {
        // An extensible type is expected, so make one of the correct type
        //
        // Note: An abstract extensible class is actually allowed to be created
        // here
        create_type = targetType
    } else {
        if IsIRI(type_iri)  {
            // It's not clear exactly which type should be created. Search through
            // all types and collect a list of possible Extensible types that are
            // valid in this location.
            possible := []SHACLType{}
            for _, v := range objectTypes {
                if ! v.IsExtensible() {
                    continue
                }

                if v.IsAbstract() {
                    continue
                }

                // If a type was specified, only subclasses of that type are
                // allowed
                if targetType != nil && ! v.IsSubClassOf(targetType) {
                    continue
                }

                possible = append(possible, v)
            }

            // Sort for determinism
            sort.Slice(possible, func(i, j int) bool {
                return possible[i].GetTypeIRI() < possible[j].GetTypeIRI()
            })

            for _, t := range(possible) {
                // Ignore errors
                o, err := DecodeSHACLObject[T](data, path, context, t)
                if err == nil {
                    o.setTypeIRI(type_iri)
                    return o, nil
                }
            }
        }
        return *new(T), &DecodeError{path, "Unable to create object of type '" + type_iri + "' (no matching extensible object)"}
    }

    obj, ok := create_type.Create().(T)
    if ! ok {
        return *new(T), &DecodeError{path, "Unable to create object of type '" + type_iri + "'"}
    }
    obj.setType(create_type)
    obj.setTypeIRI(type_iri)

    for k, v := range dict {
        if k == "@type" {
            continue
        }
        if k == "@type" {
            continue
        }

        sub_path := path.PushPath(k)
        found, err := create_type.DecodeProperty(obj, k, v, sub_path)
        if err != nil {
            return *new(T), err
        }
        if ! found {
            return *new(T), &DecodeError{path, "Unknown property '" + k + "'"}
        }
    }

    return obj, nil
}

func DecodeRef[T SHACLObject](data any, path Path, context map[string]string, typ SHACLType) (Ref[T], error) {
    switch data.(type) {
    case string:
        s, err := DecodeIRI(data, path, context)
        if err != nil {
            return nil, err
        }
        return MakeIRIRef[T](s), nil
    }

    obj, err := DecodeSHACLObject[T](data, path, context, typ)
    if err != nil {
        return nil, err
    }

    return MakeObjectRef[T](obj), nil
}

func EncodeRef[T SHACLObject](value Ref[T], path Path, context map[string]string) any {
    if value.IsIRI() {
        v := value.GetIRI()
        compact, ok := context[v]
        if ok {
            return compact
        }
        return v
    }
    d := make(map[string]any)
    value.GetObj().EncodeProperties(d, path)
    return d
}

func DecodeString(data any, path Path, context map[string]string) (string, error) {
    v, ok := data.(string)
    if ! ok {
        return v, &DecodeError{path, "String expected. Got " + reflect.TypeOf(data).Name()}
    }
    return v, nil
}

func EncodeString(value string, path Path, context map[string]string) any {
    return value
}

func DecodeIRI(data any, path Path, context map[string]string) (string, error) {
    s, err := DecodeString(data, path, context)
    if err != nil {
        return s, err
    }

    for k, v := range context {
        if s == v {
            s = k
            break
        }
    }

    if ! IsBlankNode(s) && ! IsIRI(s) {
        return s, &DecodeError{path, "Must be blank node or IRI. Got '" + s + "'"}
    }

    return s, nil
}

func EncodeIRI(value string, path Path, context map[string]string) any {
    compact, ok := context[value]
    if ok {
        return compact
    }
    return value
}

func DecodeBoolean(data any, path Path, context map[string]string) (bool, error) {
    v, ok := data.(bool)
    if ! ok {
        return v, &DecodeError{path, "Boolean expected. Got " + reflect.TypeOf(data).Name()}
    }
    return v, nil
}

func EncodeBoolean(value bool, path Path, context map[string]string) any {
    return value
}

func DecodeInteger(data any, path Path, context map[string]string) (int, error) {
    switch data.(type) {
    case int:
        return data.(int), nil
    case float64:
        v := data.(float64)
        if v == float64(int64(v)) {
            return int(v), nil
        }
        return 0, &DecodeError{path, "Value must be an integer. Got " + fmt.Sprintf("%f", v)}
    default:
        return 0, &DecodeError{path, "Integer expected. Got " + reflect.TypeOf(data).Name()}
    }
}

func EncodeInteger(value int, path Path, context map[string]string) any {
    return value
}

func DecodeFloat(data any, path Path, context map[string]string) (float64, error) {
    switch data.(type) {
    case float64:
        return data.(float64), nil
    case string:
        v, err := strconv.ParseFloat(data.(string), 64)
        if err != nil {
            return 0, err
        }
        return v, nil
    default:
        return 0, &DecodeError{path, "Float expected. Got " + reflect.TypeOf(data).Name()}
    }
}

func EncodeFloat(value float64, path Path, context map[string]string) any {
    return strconv.FormatFloat(value, 'f', -1, 64)
}

const UtcFormatStr = "%Y-%m-%dT%H:%M:%SZ"
const TzFormatStr = "%Y-%m-%dT%H:%M:%S%:z"

func decodeDateTimeString(data any, path Path, re *regexp.Regexp) (time.Time, error) {
    v, ok := data.(string)
    if ! ok {
        return time.Time{}, &DecodeError{path, "String expected. Got " + reflect.TypeOf(data).Name()}
    }

    match := re.FindStringSubmatch(v)

    if match == nil {
        return time.Time{}, &DecodeError{path, "Invalid date time string '" + v + "'"}
    }

    var format string
    s := match[1]
    tzstr := match[2]

    switch tzstr {
    case "Z":
        s += "+00:00"
        format = "%Y-%m-%dT%H:%M:%S%:z"
    case "":
        format = "%Y-%m-%dT%H:%M:%S"
    default:
        s += tzstr
        format = "%Y-%m-%dT%H:%M:%S%:z"
    }

    t, err := strftime.Parse(format, v)
    if err != nil {
        return time.Time{}, &DecodeError{path, "Invalid date time string '" + v + "': " + err.Error()}
    }
    return t, nil
}

var dateTimeRegex = regexp.MustCompile(`^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(Z|[+-]\d{2}:\d{2})?$`)
func DecodeDateTime(data any, path Path, context map[string]string) (time.Time, error) {
    return decodeDateTimeString(data, path, dateTimeRegex)
}

var dateTimeStampRegex = regexp.MustCompile(`^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(Z|[+-]\d{2}:\d{2})$`)
func DecodeDateTimeStamp(data any, path Path, context map[string]string) (time.Time, error) {
    return decodeDateTimeString(data, path, dateTimeStampRegex)
}

func EncodeDateTime(value time.Time, path Path, context map[string]string) any {
    if value.Location() == time.UTC {
        return strftime.Format(UtcFormatStr, value)
    }
    return strftime.Format(TzFormatStr, value)
}

func DecodeList[T any](data any, path Path, context map[string]string, f func (any, Path, map[string]string) (T, error)) ([]T, error) {
    lst, ok := data.([]interface{})
    if ! ok {
        return nil, &DecodeError{path, "Must be a list"}
    }

    var result []T
    for idx, v := range lst {
        sub_path := path.PushIndex(idx)
        item, err := f(v, sub_path, context)
        if err != nil {
            return nil, err
        }
        result = append(result, item)
    }

    return result, nil
}

func EncodeList[T any](value []T, path Path, context map[string]string, f func (T, Path, map[string]string) any) any {
    lst := []any{}
    for idx, v := range value {
        lst = append(lst, f(v, path.PushIndex(idx), context))
    }
    return lst
}

// IRI Validation
func IsIRI(iri string) bool {
    if strings.HasPrefix(iri, "_:") {
        return false
    }
    if strings.Contains(iri, ":") {
        return true
    }
    return false
}

func IsBlankNode(iri string) bool {
    return strings.HasPrefix(iri, "_:")
}

// Optional
type Optional[T any] struct {
    value *T
}

func (self Optional[T]) Get() T {
    return *self.value
}

func (self Optional[T]) GetDefault(val T) T {
    if ! self.IsSet() {
        return val
    }
    return *self.value
}

func (self Optional[T]) IsSet() bool {
    return self.value != nil
}

func NewOptional[T any](value T) Optional[T] {
    return Optional[T]{&value}
}

func NewEmptyOptional[T any]() Optional[T] {
    return Optional[T]{nil}
}

// Validator
type Validator[T any] interface {
    Check(T, string) error
}

func ValueToString(val any) string {
    switch val.(type) {
    case string:
        return val.(string)
    case int:
        return strconv.Itoa(val.(int))
    case time.Time:
        t := val.(time.Time)
        if t.Location() == time.UTC {
            return strftime.Format(UtcFormatStr, t)
        }
        return strftime.Format(TzFormatStr, t)
    }
    panic("Unsupported Type " + reflect.TypeOf(val).Name())
}


// ID Validator
type IDValidator struct {}

func (self IDValidator) Check(val string, name string) error {
    if ! IsIRI(val) && ! IsBlankNode(val) {
        return &ValidationError{name, "Must be an IRI or a Blank Node"}
    }
    return nil
}


// Regex Validator
type RegexValidator[T int | time.Time | string] struct {
    Regex string
}

func (self RegexValidator[T]) Check(val T, name string) error {
    s := ValueToString(val)

    m, err := regexp.MatchString(self.Regex, s)
    if err != nil {
        return err
    }
    if ! m {
        return &ValidationError{name, "Value '" + s + "' does not match pattern"}
    }
    return nil
}

// Integer Min Validator
type IntegerMinValidator struct {
    Min int
}

func (self IntegerMinValidator) Check(val int, name string) error {
    if val < self.Min {
        return &ValidationError{name, "Value " + strconv.Itoa(val) + " is less than minimum " + strconv.Itoa(self.Min)}
    }
    return nil
}

// Integer Max Validator
type IntegerMaxValidator struct {
    Max int
}

func (self IntegerMaxValidator) Check(val int, name string) error {
    if val > self.Max {
        return &ValidationError{name, "Value " + strconv.Itoa(val) + " is greater than maximum" + strconv.Itoa(self.Max)}
    }
    return nil
}

// Enum Validator
type EnumValidator struct {
    Values []string
}

func (self EnumValidator) Check(val string, name string) error {
    for _, v := range self.Values {
        if val == v {
            return nil
        }
    }
    return &ValidationError{name, "Value '" + val + "' is not a valid enumerated value" }
}

// Property
type PropertyInterface[T any] interface {
    Get() T
    Set(val T) error
    Delete()
    IsSet() bool
    Walk(path Path, visit Visit)
}

type Property[T any] struct {
    value Optional[T]
    name string
    validators []Validator[T]
}

func NewProperty[T any](name string, validators []Validator[T]) Property[T] {
    return Property[T]{
        value: NewEmptyOptional[T](),
        name: name,
        validators: validators,
    }
}

func (self *Property[T]) Get() T {
    return self.value.Get()
}

func (self *Property[T]) Set(val T) error {
    for _, validator := range self.validators {
        err := validator.Check(val, self.name)
        if err != nil {
            return err
        }
    }

    self.value = NewOptional(val)
    return nil
}

func (self *Property[T]) Delete() {
    self.value = NewEmptyOptional[T]()
}

func (self *Property[T]) IsSet() bool {
    return self.value.IsSet()
}

func (self *Property[T]) Check(path Path, handler ErrorHandler) bool {
    if ! self.value.IsSet() {
        return true
    }

    var valid bool
    valid = true

    for _, validator := range self.validators {
        err := validator.Check(self.value.Get(), self.name)
        if err != nil {
            if handler != nil {
                handler.HandleError(err, path)
            }
            valid = false
        }
    }
    return valid
}

func (self *Property[T]) Walk(path Path, visit Visit) {
    if ! self.value.IsSet() {
        return
    }

    visit(path.PushPath(self.name), self.value.Get())
}

// Ref Property
type RefPropertyInterface[T SHACLObject] interface {
    PropertyInterface[Ref[T]]

    GetIRI() string
    GetObj() T
    IsObj() bool
    IsIRI() bool
}

type RefProperty[T SHACLObject] struct {
    Property[Ref[T]]
}

func NewRefProperty[T SHACLObject](name string, validators []Validator[Ref[T]]) RefProperty[T] {
    return RefProperty[T]{
        Property: Property[Ref[T]]{
            value: NewEmptyOptional[Ref[T]](),
            name: name,
            validators: validators,
        },
    }
}

func (self *RefProperty[T]) GetIRI() string {
    return self.Get().GetIRI()
}

func (self *RefProperty[T]) GetObj() T {
    return self.Get().GetObj()
}

func (self *RefProperty[T]) IsSet() bool {
    return self.Property.IsSet() && self.Get().IsSet()
}

func (self *RefProperty[T]) IsObj() bool {
    return self.Property.IsSet() && self.Get().IsObj()
}

func (self *RefProperty[T]) IsIRI() bool {
    return self.Property.IsSet() && self.Get().IsIRI()
}

func (self *RefProperty[T]) Walk(path Path, visit Visit) {
    if ! self.IsSet() {
        return
    }

    r, err := ConvertRef[SHACLObject](self.value.Get())
    if err != nil {
        return
    }

    visit(path.PushPath(self.name), r)
}

// List Property
type ListPropertyInterface[T any] interface {
    Get() []T
    Set(val []T) error
    Delete()
    Walk(path Path, visit Visit)
    IsSet() bool
}

type ListProperty[T any] struct {
    value []T
    name string
    validators []Validator[T]
}

func NewListProperty[T any](name string, validators []Validator[T]) ListProperty[T] {
    return ListProperty[T]{
        value: []T{},
        name: name,
        validators: validators,
    }
}

func (self *ListProperty[T]) Get() []T {
    return self.value
}

func (self *ListProperty[T]) Set(val []T) error {
    for _, v := range val {
        for _, validator := range self.validators {
            err := validator.Check(v, self.name)
            if err != nil {
                return err
            }
        }
    }

    self.value = val
    return nil
}

func (self *ListProperty[T]) Delete() {
    self.value = []T{}
}

func (self *ListProperty[T]) IsSet() bool {
    return self.value != nil && len(self.value) > 0
}

func (self *ListProperty[T]) Check(path Path, handler ErrorHandler) bool {
    var valid bool
    valid = true

    for idx, v := range self.value {
        for _, validator := range self.validators {
            err := validator.Check(v, self.name)
            if err != nil {
                if handler != nil {
                    handler.HandleError(err, path.PushIndex(idx))
                }
                valid = false
            }
        }
    }
    return valid
}

func (self *ListProperty[T]) Walk(path Path, visit Visit) {
    sub_path := path.PushPath(self.name)

    for idx, v := range self.value {
        visit(sub_path.PushIndex(idx), v)
    }
}

type RefListProperty[T SHACLObject] struct {
    ListProperty[Ref[T]]
}

func NewRefListProperty[T SHACLObject](name string, validators []Validator[Ref[T]]) RefListProperty[T] {
    return RefListProperty[T]{
        ListProperty: ListProperty[Ref[T]]{
            value: []Ref[T]{},
            name: name,
            validators: validators,
        },
    }
}

func (self *RefListProperty[T]) Walk(path Path, visit Visit) {
    sub_path := path.PushPath(self.name)

    for idx, v := range self.value {
        r, err := ConvertRef[SHACLObject](v)
        if err != nil {
            visit(sub_path.PushIndex(idx), r)
        }
    }
}


// An Abstract class
type AbstractClassObject struct {
    SHACLObjectBase

}


type AbstractClassObjectType struct {
    SHACLTypeBase
}
var abstractClassType AbstractClassObjectType

func DecodeAbstractClass (data any, path Path, context map[string]string) (Ref[AbstractClass], error) {
    return DecodeRef[AbstractClass](data, path, context, abstractClassType)
}

func (self AbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(AbstractClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self AbstractClassObjectType) Create() SHACLObject {
    return ConstructAbstractClassObject(&AbstractClassObject{})
}

func ConstructAbstractClassObject(o *AbstractClassObject) *AbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type AbstractClass interface {
    SHACLObject
}



func (self *AbstractClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *AbstractClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *AbstractClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}
type AbstractShClassObject struct {
    SHACLObjectBase

}


type AbstractShClassObjectType struct {
    SHACLTypeBase
}
var abstractShClassType AbstractShClassObjectType

func DecodeAbstractShClass (data any, path Path, context map[string]string) (Ref[AbstractShClass], error) {
    return DecodeRef[AbstractShClass](data, path, context, abstractShClassType)
}

func (self AbstractShClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(AbstractShClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self AbstractShClassObjectType) Create() SHACLObject {
    return ConstructAbstractShClassObject(&AbstractShClassObject{})
}

func ConstructAbstractShClassObject(o *AbstractShClassObject) *AbstractShClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type AbstractShClass interface {
    SHACLObject
}



func (self *AbstractShClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *AbstractShClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *AbstractShClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An Abstract class using the SPDX type
type AbstractSpdxClassObject struct {
    SHACLObjectBase

}


type AbstractSpdxClassObjectType struct {
    SHACLTypeBase
}
var abstractSpdxClassType AbstractSpdxClassObjectType

func DecodeAbstractSpdxClass (data any, path Path, context map[string]string) (Ref[AbstractSpdxClass], error) {
    return DecodeRef[AbstractSpdxClass](data, path, context, abstractSpdxClassType)
}

func (self AbstractSpdxClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(AbstractSpdxClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self AbstractSpdxClassObjectType) Create() SHACLObject {
    return ConstructAbstractSpdxClassObject(&AbstractSpdxClassObject{})
}

func ConstructAbstractSpdxClassObject(o *AbstractSpdxClassObject) *AbstractSpdxClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type AbstractSpdxClass interface {
    SHACLObject
}



func (self *AbstractSpdxClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *AbstractSpdxClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *AbstractSpdxClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A concrete class
type ConcreteClassObject struct {
    AbstractClassObject

}


type ConcreteClassObjectType struct {
    SHACLTypeBase
}
var concreteClassType ConcreteClassObjectType

func DecodeConcreteClass (data any, path Path, context map[string]string) (Ref[ConcreteClass], error) {
    return DecodeRef[ConcreteClass](data, path, context, concreteClassType)
}

func (self ConcreteClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ConcreteClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self ConcreteClassObjectType) Create() SHACLObject {
    return ConstructConcreteClassObject(&ConcreteClassObject{})
}

func ConstructConcreteClassObject(o *ConcreteClassObject) *ConcreteClassObject {
    ConstructAbstractClassObject(&o.AbstractClassObject)
    return o
}

type ConcreteClass interface {
    AbstractClass
}


func MakeConcreteClass() ConcreteClass {
    return ConstructConcreteClassObject(&ConcreteClassObject{})
}

func MakeConcreteClassRef() Ref[ConcreteClass] {
    o := MakeConcreteClass()
    return MakeObjectRef[ConcreteClass](o)
}

func (self *ConcreteClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.AbstractClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *ConcreteClassObject) Walk(path Path, visit Visit) {
    self.AbstractClassObject.Walk(path, visit)
}



func (self *ConcreteClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.AbstractClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A concrete class
type ConcreteShClassObject struct {
    AbstractShClassObject

}


type ConcreteShClassObjectType struct {
    SHACLTypeBase
}
var concreteShClassType ConcreteShClassObjectType

func DecodeConcreteShClass (data any, path Path, context map[string]string) (Ref[ConcreteShClass], error) {
    return DecodeRef[ConcreteShClass](data, path, context, concreteShClassType)
}

func (self ConcreteShClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ConcreteShClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self ConcreteShClassObjectType) Create() SHACLObject {
    return ConstructConcreteShClassObject(&ConcreteShClassObject{})
}

func ConstructConcreteShClassObject(o *ConcreteShClassObject) *ConcreteShClassObject {
    ConstructAbstractShClassObject(&o.AbstractShClassObject)
    return o
}

type ConcreteShClass interface {
    AbstractShClass
}


func MakeConcreteShClass() ConcreteShClass {
    return ConstructConcreteShClassObject(&ConcreteShClassObject{})
}

func MakeConcreteShClassRef() Ref[ConcreteShClass] {
    o := MakeConcreteShClass()
    return MakeObjectRef[ConcreteShClass](o)
}

func (self *ConcreteShClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.AbstractShClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *ConcreteShClassObject) Walk(path Path, visit Visit) {
    self.AbstractShClassObject.Walk(path, visit)
}



func (self *ConcreteShClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.AbstractShClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A concrete class
type ConcreteSpdxClassObject struct {
    AbstractSpdxClassObject

}


type ConcreteSpdxClassObjectType struct {
    SHACLTypeBase
}
var concreteSpdxClassType ConcreteSpdxClassObjectType

func DecodeConcreteSpdxClass (data any, path Path, context map[string]string) (Ref[ConcreteSpdxClass], error) {
    return DecodeRef[ConcreteSpdxClass](data, path, context, concreteSpdxClassType)
}

func (self ConcreteSpdxClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ConcreteSpdxClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self ConcreteSpdxClassObjectType) Create() SHACLObject {
    return ConstructConcreteSpdxClassObject(&ConcreteSpdxClassObject{})
}

func ConstructConcreteSpdxClassObject(o *ConcreteSpdxClassObject) *ConcreteSpdxClassObject {
    ConstructAbstractSpdxClassObject(&o.AbstractSpdxClassObject)
    return o
}

type ConcreteSpdxClass interface {
    AbstractSpdxClass
}


func MakeConcreteSpdxClass() ConcreteSpdxClass {
    return ConstructConcreteSpdxClassObject(&ConcreteSpdxClassObject{})
}

func MakeConcreteSpdxClassRef() Ref[ConcreteSpdxClass] {
    o := MakeConcreteSpdxClass()
    return MakeObjectRef[ConcreteSpdxClass](o)
}

func (self *ConcreteSpdxClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.AbstractSpdxClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *ConcreteSpdxClassObject) Walk(path Path, visit Visit) {
    self.AbstractSpdxClassObject.Walk(path, visit)
}



func (self *ConcreteSpdxClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.AbstractSpdxClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An enumerated type
type EnumTypeObject struct {
    SHACLObjectBase

}

// The foo value of enumType
const EnumTypeFoo = "http://example.org/enumType/foo"
// The bar value of enumType
const EnumTypeBar = "http://example.org/enumType/bar"
// This value has no label
const EnumTypeNolabel = "http://example.org/enumType/nolabel"

type EnumTypeObjectType struct {
    SHACLTypeBase
}
var enumTypeType EnumTypeObjectType

func DecodeEnumType (data any, path Path, context map[string]string) (Ref[EnumType], error) {
    return DecodeRef[EnumType](data, path, context, enumTypeType)
}

func (self EnumTypeObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(EnumType)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self EnumTypeObjectType) Create() SHACLObject {
    return ConstructEnumTypeObject(&EnumTypeObject{})
}

func ConstructEnumTypeObject(o *EnumTypeObject) *EnumTypeObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type EnumType interface {
    SHACLObject
}


func MakeEnumType() EnumType {
    return ConstructEnumTypeObject(&EnumTypeObject{})
}

func MakeEnumTypeRef() Ref[EnumType] {
    o := MakeEnumType()
    return MakeObjectRef[EnumType](o)
}

func (self *EnumTypeObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *EnumTypeObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *EnumTypeObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An extensible abstract class
type ExtensibleAbstractClassObject struct {
    SHACLObjectBase
    SHACLExtensibleBase

}


type ExtensibleAbstractClassObjectType struct {
    SHACLTypeBase
}
var extensibleAbstractClassType ExtensibleAbstractClassObjectType

func DecodeExtensibleAbstractClass (data any, path Path, context map[string]string) (Ref[ExtensibleAbstractClass], error) {
    return DecodeRef[ExtensibleAbstractClass](data, path, context, extensibleAbstractClassType)
}

func (self ExtensibleAbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ExtensibleAbstractClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self ExtensibleAbstractClassObjectType) Create() SHACLObject {
    return ConstructExtensibleAbstractClassObject(&ExtensibleAbstractClassObject{})
}

func ConstructExtensibleAbstractClassObject(o *ExtensibleAbstractClassObject) *ExtensibleAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type ExtensibleAbstractClass interface {
    SHACLObject
}



func (self *ExtensibleAbstractClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *ExtensibleAbstractClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *ExtensibleAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    self.SHACLExtensibleBase.EncodeExtProperties(data, path)
    return nil
}

// A class with an ID alias
type IdPropClassObject struct {
    SHACLObjectBase

}


type IdPropClassObjectType struct {
    SHACLTypeBase
}
var idPropClassType IdPropClassObjectType

func DecodeIdPropClass (data any, path Path, context map[string]string) (Ref[IdPropClass], error) {
    return DecodeRef[IdPropClass](data, path, context, idPropClassType)
}

func (self IdPropClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(IdPropClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self IdPropClassObjectType) Create() SHACLObject {
    return ConstructIdPropClassObject(&IdPropClassObject{})
}

func ConstructIdPropClassObject(o *IdPropClassObject) *IdPropClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type IdPropClass interface {
    SHACLObject
}


func MakeIdPropClass() IdPropClass {
    return ConstructIdPropClassObject(&IdPropClassObject{})
}

func MakeIdPropClassRef() Ref[IdPropClass] {
    o := MakeIdPropClass()
    return MakeObjectRef[IdPropClass](o)
}

func (self *IdPropClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *IdPropClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *IdPropClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that inherits its idPropertyName from the parent
type InheritedIdPropClassObject struct {
    IdPropClassObject

}


type InheritedIdPropClassObjectType struct {
    SHACLTypeBase
}
var inheritedIdPropClassType InheritedIdPropClassObjectType

func DecodeInheritedIdPropClass (data any, path Path, context map[string]string) (Ref[InheritedIdPropClass], error) {
    return DecodeRef[InheritedIdPropClass](data, path, context, inheritedIdPropClassType)
}

func (self InheritedIdPropClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(InheritedIdPropClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self InheritedIdPropClassObjectType) Create() SHACLObject {
    return ConstructInheritedIdPropClassObject(&InheritedIdPropClassObject{})
}

func ConstructInheritedIdPropClassObject(o *InheritedIdPropClassObject) *InheritedIdPropClassObject {
    ConstructIdPropClassObject(&o.IdPropClassObject)
    return o
}

type InheritedIdPropClass interface {
    IdPropClass
}


func MakeInheritedIdPropClass() InheritedIdPropClass {
    return ConstructInheritedIdPropClassObject(&InheritedIdPropClassObject{})
}

func MakeInheritedIdPropClassRef() Ref[InheritedIdPropClass] {
    o := MakeInheritedIdPropClass()
    return MakeObjectRef[InheritedIdPropClass](o)
}

func (self *InheritedIdPropClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.IdPropClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *InheritedIdPropClassObject) Walk(path Path, visit Visit) {
    self.IdPropClassObject.Walk(path, visit)
}



func (self *InheritedIdPropClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.IdPropClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class to test links
type LinkClassObject struct {
    SHACLObjectBase

    // A link to an extensible-class
    linkClassExtensible RefProperty[ExtensibleClass]
    // A link-class list property
    linkClassLinkListProp RefListProperty[LinkClass]
    // A link-class property
    linkClassLinkProp RefProperty[LinkClass]
    // A link-class property with no sh:class
    linkClassLinkPropNoClass RefProperty[LinkClass]
}


type LinkClassObjectType struct {
    SHACLTypeBase
}
var linkClassType LinkClassObjectType
var linkClassLinkClassExtensibleContext = map[string]string{}
var linkClassLinkClassLinkListPropContext = map[string]string{}
var linkClassLinkClassLinkPropContext = map[string]string{}
var linkClassLinkClassLinkPropNoClassContext = map[string]string{}

func DecodeLinkClass (data any, path Path, context map[string]string) (Ref[LinkClass], error) {
    return DecodeRef[LinkClass](data, path, context, linkClassType)
}

func (self LinkClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(LinkClass)
    _ = obj
    switch name {
    case "http://example.org/link-class-extensible", "link-class-extensible":
        val, err := DecodeExtensibleClass(value, path, linkClassLinkClassExtensibleContext)
        if err != nil {
            return false, err
        }
        err = obj.LinkClassExtensible().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-list-prop", "link-class-link-list-prop":
        val, err := DecodeList[Ref[LinkClass]](value, path, linkClassLinkClassLinkListPropContext, DecodeLinkClass)
        if err != nil {
            return false, err
        }
        err = obj.LinkClassLinkListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-prop", "link-class-link-prop":
        val, err := DecodeLinkClass(value, path, linkClassLinkClassLinkPropContext)
        if err != nil {
            return false, err
        }
        err = obj.LinkClassLinkProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-prop-no-class", "link-class-link-prop-no-class":
        val, err := DecodeLinkClass(value, path, linkClassLinkClassLinkPropNoClassContext)
        if err != nil {
            return false, err
        }
        err = obj.LinkClassLinkPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self LinkClassObjectType) Create() SHACLObject {
    return ConstructLinkClassObject(&LinkClassObject{})
}

func ConstructLinkClassObject(o *LinkClassObject) *LinkClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    {
        validators := []Validator[Ref[ExtensibleClass]]{}
        o.linkClassExtensible = NewRefProperty[ExtensibleClass]("linkClassExtensible", validators)
    }
    {
        validators := []Validator[Ref[LinkClass]]{}
        o.linkClassLinkListProp = NewRefListProperty[LinkClass]("linkClassLinkListProp", validators)
    }
    {
        validators := []Validator[Ref[LinkClass]]{}
        o.linkClassLinkProp = NewRefProperty[LinkClass]("linkClassLinkProp", validators)
    }
    {
        validators := []Validator[Ref[LinkClass]]{}
        o.linkClassLinkPropNoClass = NewRefProperty[LinkClass]("linkClassLinkPropNoClass", validators)
    }
    return o
}

type LinkClass interface {
    SHACLObject
    LinkClassExtensible() RefPropertyInterface[ExtensibleClass]
    LinkClassLinkListProp() ListPropertyInterface[Ref[LinkClass]]
    LinkClassLinkProp() RefPropertyInterface[LinkClass]
    LinkClassLinkPropNoClass() RefPropertyInterface[LinkClass]
}


func MakeLinkClass() LinkClass {
    return ConstructLinkClassObject(&LinkClassObject{})
}

func MakeLinkClassRef() Ref[LinkClass] {
    o := MakeLinkClass()
    return MakeObjectRef[LinkClass](o)
}

func (self *LinkClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("linkClassExtensible")
        if ! self.linkClassExtensible.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("linkClassLinkListProp")
        if ! self.linkClassLinkListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("linkClassLinkProp")
        if ! self.linkClassLinkProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("linkClassLinkPropNoClass")
        if ! self.linkClassLinkPropNoClass.Check(prop_path, handler) {
            valid = false
        }
    }
    return valid
}

func (self *LinkClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
    self.linkClassExtensible.Walk(path, visit)
    self.linkClassLinkListProp.Walk(path, visit)
    self.linkClassLinkProp.Walk(path, visit)
    self.linkClassLinkPropNoClass.Walk(path, visit)
}


func (self *LinkClassObject) LinkClassExtensible() RefPropertyInterface[ExtensibleClass] { return &self.linkClassExtensible }
func (self *LinkClassObject) LinkClassLinkListProp() ListPropertyInterface[Ref[LinkClass]] { return &self.linkClassLinkListProp }
func (self *LinkClassObject) LinkClassLinkProp() RefPropertyInterface[LinkClass] { return &self.linkClassLinkProp }
func (self *LinkClassObject) LinkClassLinkPropNoClass() RefPropertyInterface[LinkClass] { return &self.linkClassLinkPropNoClass }

func (self *LinkClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.linkClassExtensible.IsSet() {
        data["link-class-extensible"] = EncodeRef[ExtensibleClass](self.linkClassExtensible.Get(), path.PushPath("linkClassExtensible"), linkClassLinkClassExtensibleContext)
    }
    if self.linkClassLinkListProp.IsSet() {
        data["link-class-link-list-prop"] = EncodeList[Ref[LinkClass]](self.linkClassLinkListProp.Get(), path.PushPath("linkClassLinkListProp"), linkClassLinkClassLinkListPropContext, EncodeRef[LinkClass])
    }
    if self.linkClassLinkProp.IsSet() {
        data["link-class-link-prop"] = EncodeRef[LinkClass](self.linkClassLinkProp.Get(), path.PushPath("linkClassLinkProp"), linkClassLinkClassLinkPropContext)
    }
    if self.linkClassLinkPropNoClass.IsSet() {
        data["link-class-link-prop-no-class"] = EncodeRef[LinkClass](self.linkClassLinkPropNoClass.Get(), path.PushPath("linkClassLinkPropNoClass"), linkClassLinkClassLinkPropNoClassContext)
    }
    return nil
}

// A class derived from link-class
type LinkDerivedClassObject struct {
    LinkClassObject

}


type LinkDerivedClassObjectType struct {
    SHACLTypeBase
}
var linkDerivedClassType LinkDerivedClassObjectType

func DecodeLinkDerivedClass (data any, path Path, context map[string]string) (Ref[LinkDerivedClass], error) {
    return DecodeRef[LinkDerivedClass](data, path, context, linkDerivedClassType)
}

func (self LinkDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(LinkDerivedClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self LinkDerivedClassObjectType) Create() SHACLObject {
    return ConstructLinkDerivedClassObject(&LinkDerivedClassObject{})
}

func ConstructLinkDerivedClassObject(o *LinkDerivedClassObject) *LinkDerivedClassObject {
    ConstructLinkClassObject(&o.LinkClassObject)
    return o
}

type LinkDerivedClass interface {
    LinkClass
}


func MakeLinkDerivedClass() LinkDerivedClass {
    return ConstructLinkDerivedClassObject(&LinkDerivedClassObject{})
}

func MakeLinkDerivedClassRef() Ref[LinkDerivedClass] {
    o := MakeLinkDerivedClass()
    return MakeObjectRef[LinkDerivedClass](o)
}

func (self *LinkDerivedClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.LinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *LinkDerivedClassObject) Walk(path Path, visit Visit) {
    self.LinkClassObject.Walk(path, visit)
}



func (self *LinkDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.LinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that must be a blank node
type NodeKindBlankObject struct {
    LinkClassObject

}


type NodeKindBlankObjectType struct {
    SHACLTypeBase
}
var nodeKindBlankType NodeKindBlankObjectType

func DecodeNodeKindBlank (data any, path Path, context map[string]string) (Ref[NodeKindBlank], error) {
    return DecodeRef[NodeKindBlank](data, path, context, nodeKindBlankType)
}

func (self NodeKindBlankObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(NodeKindBlank)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self NodeKindBlankObjectType) Create() SHACLObject {
    return ConstructNodeKindBlankObject(&NodeKindBlankObject{})
}

func ConstructNodeKindBlankObject(o *NodeKindBlankObject) *NodeKindBlankObject {
    ConstructLinkClassObject(&o.LinkClassObject)
    return o
}

type NodeKindBlank interface {
    LinkClass
}


func MakeNodeKindBlank() NodeKindBlank {
    return ConstructNodeKindBlankObject(&NodeKindBlankObject{})
}

func MakeNodeKindBlankRef() Ref[NodeKindBlank] {
    o := MakeNodeKindBlank()
    return MakeObjectRef[NodeKindBlank](o)
}

func (self *NodeKindBlankObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.LinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *NodeKindBlankObject) Walk(path Path, visit Visit) {
    self.LinkClassObject.Walk(path, visit)
}



func (self *NodeKindBlankObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.LinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that must be an IRI
type NodeKindIriObject struct {
    LinkClassObject

}


type NodeKindIriObjectType struct {
    SHACLTypeBase
}
var nodeKindIriType NodeKindIriObjectType

func DecodeNodeKindIri (data any, path Path, context map[string]string) (Ref[NodeKindIri], error) {
    return DecodeRef[NodeKindIri](data, path, context, nodeKindIriType)
}

func (self NodeKindIriObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(NodeKindIri)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self NodeKindIriObjectType) Create() SHACLObject {
    return ConstructNodeKindIriObject(&NodeKindIriObject{})
}

func ConstructNodeKindIriObject(o *NodeKindIriObject) *NodeKindIriObject {
    ConstructLinkClassObject(&o.LinkClassObject)
    return o
}

type NodeKindIri interface {
    LinkClass
}


func MakeNodeKindIri() NodeKindIri {
    return ConstructNodeKindIriObject(&NodeKindIriObject{})
}

func MakeNodeKindIriRef() Ref[NodeKindIri] {
    o := MakeNodeKindIri()
    return MakeObjectRef[NodeKindIri](o)
}

func (self *NodeKindIriObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.LinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *NodeKindIriObject) Walk(path Path, visit Visit) {
    self.LinkClassObject.Walk(path, visit)
}



func (self *NodeKindIriObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.LinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that can be either a blank node or an IRI
type NodeKindIriOrBlankObject struct {
    LinkClassObject

}


type NodeKindIriOrBlankObjectType struct {
    SHACLTypeBase
}
var nodeKindIriOrBlankType NodeKindIriOrBlankObjectType

func DecodeNodeKindIriOrBlank (data any, path Path, context map[string]string) (Ref[NodeKindIriOrBlank], error) {
    return DecodeRef[NodeKindIriOrBlank](data, path, context, nodeKindIriOrBlankType)
}

func (self NodeKindIriOrBlankObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(NodeKindIriOrBlank)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self NodeKindIriOrBlankObjectType) Create() SHACLObject {
    return ConstructNodeKindIriOrBlankObject(&NodeKindIriOrBlankObject{})
}

func ConstructNodeKindIriOrBlankObject(o *NodeKindIriOrBlankObject) *NodeKindIriOrBlankObject {
    ConstructLinkClassObject(&o.LinkClassObject)
    return o
}

type NodeKindIriOrBlank interface {
    LinkClass
}


func MakeNodeKindIriOrBlank() NodeKindIriOrBlank {
    return ConstructNodeKindIriOrBlankObject(&NodeKindIriOrBlankObject{})
}

func MakeNodeKindIriOrBlankRef() Ref[NodeKindIriOrBlank] {
    o := MakeNodeKindIriOrBlank()
    return MakeObjectRef[NodeKindIriOrBlank](o)
}

func (self *NodeKindIriOrBlankObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.LinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *NodeKindIriOrBlankObject) Walk(path Path, visit Visit) {
    self.LinkClassObject.Walk(path, visit)
}



func (self *NodeKindIriOrBlankObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.LinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that is not a nodeshape
type NonShapeClassObject struct {
    SHACLObjectBase

}


type NonShapeClassObjectType struct {
    SHACLTypeBase
}
var nonShapeClassType NonShapeClassObjectType

func DecodeNonShapeClass (data any, path Path, context map[string]string) (Ref[NonShapeClass], error) {
    return DecodeRef[NonShapeClass](data, path, context, nonShapeClassType)
}

func (self NonShapeClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(NonShapeClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self NonShapeClassObjectType) Create() SHACLObject {
    return ConstructNonShapeClassObject(&NonShapeClassObject{})
}

func ConstructNonShapeClassObject(o *NonShapeClassObject) *NonShapeClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type NonShapeClass interface {
    SHACLObject
}


func MakeNonShapeClass() NonShapeClass {
    return ConstructNonShapeClassObject(&NonShapeClassObject{})
}

func MakeNonShapeClassRef() Ref[NonShapeClass] {
    o := MakeNonShapeClass()
    return MakeObjectRef[NonShapeClass](o)
}

func (self *NonShapeClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *NonShapeClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *NonShapeClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// The parent class
type ParentClassObject struct {
    SHACLObjectBase

}


type ParentClassObjectType struct {
    SHACLTypeBase
}
var parentClassType ParentClassObjectType

func DecodeParentClass (data any, path Path, context map[string]string) (Ref[ParentClass], error) {
    return DecodeRef[ParentClass](data, path, context, parentClassType)
}

func (self ParentClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ParentClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self ParentClassObjectType) Create() SHACLObject {
    return ConstructParentClassObject(&ParentClassObject{})
}

func ConstructParentClassObject(o *ParentClassObject) *ParentClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type ParentClass interface {
    SHACLObject
}


func MakeParentClass() ParentClass {
    return ConstructParentClassObject(&ParentClassObject{})
}

func MakeParentClassRef() Ref[ParentClass] {
    o := MakeParentClass()
    return MakeObjectRef[ParentClass](o)
}

func (self *ParentClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *ParentClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *ParentClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class with a mandatory abstract class
type RequiredAbstractObject struct {
    SHACLObjectBase

    // A required abstract class property
    requiredAbstractAbstractClassProp RefProperty[AbstractClass]
}


type RequiredAbstractObjectType struct {
    SHACLTypeBase
}
var requiredAbstractType RequiredAbstractObjectType
var requiredAbstractRequiredAbstractAbstractClassPropContext = map[string]string{}

func DecodeRequiredAbstract (data any, path Path, context map[string]string) (Ref[RequiredAbstract], error) {
    return DecodeRef[RequiredAbstract](data, path, context, requiredAbstractType)
}

func (self RequiredAbstractObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(RequiredAbstract)
    _ = obj
    switch name {
    case "http://example.org/required-abstract/abstract-class-prop", "required-abstract/abstract-class-prop":
        val, err := DecodeAbstractClass(value, path, requiredAbstractRequiredAbstractAbstractClassPropContext)
        if err != nil {
            return false, err
        }
        err = obj.RequiredAbstractAbstractClassProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self RequiredAbstractObjectType) Create() SHACLObject {
    return ConstructRequiredAbstractObject(&RequiredAbstractObject{})
}

func ConstructRequiredAbstractObject(o *RequiredAbstractObject) *RequiredAbstractObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    {
        validators := []Validator[Ref[AbstractClass]]{}
        o.requiredAbstractAbstractClassProp = NewRefProperty[AbstractClass]("requiredAbstractAbstractClassProp", validators)
    }
    return o
}

type RequiredAbstract interface {
    SHACLObject
    RequiredAbstractAbstractClassProp() RefPropertyInterface[AbstractClass]
}


func MakeRequiredAbstract() RequiredAbstract {
    return ConstructRequiredAbstractObject(&RequiredAbstractObject{})
}

func MakeRequiredAbstractRef() Ref[RequiredAbstract] {
    o := MakeRequiredAbstract()
    return MakeObjectRef[RequiredAbstract](o)
}

func (self *RequiredAbstractObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("requiredAbstractAbstractClassProp")
        if ! self.requiredAbstractAbstractClassProp.Check(prop_path, handler) {
            valid = false
        }
        if ! self.requiredAbstractAbstractClassProp.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"requiredAbstractAbstractClassProp", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *RequiredAbstractObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
    self.requiredAbstractAbstractClassProp.Walk(path, visit)
}


func (self *RequiredAbstractObject) RequiredAbstractAbstractClassProp() RefPropertyInterface[AbstractClass] { return &self.requiredAbstractAbstractClassProp }

func (self *RequiredAbstractObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.requiredAbstractAbstractClassProp.IsSet() {
        data["required-abstract/abstract-class-prop"] = EncodeRef[AbstractClass](self.requiredAbstractAbstractClassProp.Get(), path.PushPath("requiredAbstractAbstractClassProp"), requiredAbstractRequiredAbstractAbstractClassPropContext)
    }
    return nil
}

// Another class
type TestAnotherClassObject struct {
    SHACLObjectBase

}


type TestAnotherClassObjectType struct {
    SHACLTypeBase
}
var testAnotherClassType TestAnotherClassObjectType

func DecodeTestAnotherClass (data any, path Path, context map[string]string) (Ref[TestAnotherClass], error) {
    return DecodeRef[TestAnotherClass](data, path, context, testAnotherClassType)
}

func (self TestAnotherClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestAnotherClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self TestAnotherClassObjectType) Create() SHACLObject {
    return ConstructTestAnotherClassObject(&TestAnotherClassObject{})
}

func ConstructTestAnotherClassObject(o *TestAnotherClassObject) *TestAnotherClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type TestAnotherClass interface {
    SHACLObject
}


func MakeTestAnotherClass() TestAnotherClass {
    return ConstructTestAnotherClassObject(&TestAnotherClassObject{})
}

func MakeTestAnotherClassRef() Ref[TestAnotherClass] {
    o := MakeTestAnotherClass()
    return MakeObjectRef[TestAnotherClass](o)
}

func (self *TestAnotherClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *TestAnotherClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *TestAnotherClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// The test class
type TestClassObject struct {
    ParentClassObject

    // A property that conflicts with an existing SHACLObject property
    encode Property[string]
    // A property that is a keyword
    import_ Property[string]
    // a URI
    testClassAnyuriProp Property[string]
    // a boolean property
    testClassBooleanProp Property[bool]
    // A test-class list property
    testClassClassListProp RefListProperty[TestClass]
    // A test-class property
    testClassClassProp RefProperty[TestClass]
    // A test-class property with no sh:class
    testClassClassPropNoClass RefProperty[TestClass]
    // A datetime list property
    testClassDatetimeListProp ListProperty[time.Time]
    // A scalar datetime property
    testClassDatetimeScalarProp Property[time.Time]
    // A scalar dateTimeStamp property
    testClassDatetimestampScalarProp Property[time.Time]
    // A enum list property
    testClassEnumListProp ListProperty[string]
    // A enum property
    testClassEnumProp Property[string]
    // A enum property with no sh:class
    testClassEnumPropNoClass Property[string]
    // a float property
    testClassFloatProp Property[float64]
    // a non-negative integer
    testClassIntegerProp Property[int]
    // A named property
    namedProperty Property[string]
    // A class with no shape
    testClassNonShape RefProperty[NonShapeClass]
    // a non-negative integer
    testClassNonnegativeIntegerProp Property[int]
    // A positive integer
    testClassPositiveIntegerProp Property[int]
    // A regex validated string
    testClassRegex Property[string]
    // A regex dateTime
    testClassRegexDatetime Property[time.Time]
    // A regex dateTimeStamp
    testClassRegexDatetimestamp Property[time.Time]
    // A regex validated string list
    testClassRegexList ListProperty[string]
    // A string list property with no sh:datatype
    testClassStringListNoDatatype ListProperty[string]
    // A string list property
    testClassStringListProp ListProperty[string]
    // A scalar string propery
    testClassStringScalarProp Property[string]
}
const TestClassNamed = "http://example.org/test-class/named"

type TestClassObjectType struct {
    SHACLTypeBase
}
var testClassType TestClassObjectType
var testClassEncodeContext = map[string]string{}
var testClassImportContext = map[string]string{}
var testClassTestClassAnyuriPropContext = map[string]string{}
var testClassTestClassBooleanPropContext = map[string]string{}
var testClassTestClassClassListPropContext = map[string]string{
    "http://example.org/test-class/named": "named",}
var testClassTestClassClassPropContext = map[string]string{
    "http://example.org/test-class/named": "named",}
var testClassTestClassClassPropNoClassContext = map[string]string{
    "http://example.org/test-class/named": "named",}
var testClassTestClassDatetimeListPropContext = map[string]string{}
var testClassTestClassDatetimeScalarPropContext = map[string]string{}
var testClassTestClassDatetimestampScalarPropContext = map[string]string{}
var testClassTestClassEnumListPropContext = map[string]string{
    "http://example.org/enumType/bar": "bar",
    "http://example.org/enumType/foo": "foo",
    "http://example.org/enumType/nolabel": "nolabel",
    "http://example.org/enumType/non-named-individual": "non-named-individual",}
var testClassTestClassEnumPropContext = map[string]string{
    "http://example.org/enumType/bar": "bar",
    "http://example.org/enumType/foo": "foo",
    "http://example.org/enumType/nolabel": "nolabel",
    "http://example.org/enumType/non-named-individual": "non-named-individual",}
var testClassTestClassEnumPropNoClassContext = map[string]string{
    "http://example.org/enumType/bar": "bar",
    "http://example.org/enumType/foo": "foo",
    "http://example.org/enumType/nolabel": "nolabel",
    "http://example.org/enumType/non-named-individual": "non-named-individual",}
var testClassTestClassFloatPropContext = map[string]string{}
var testClassTestClassIntegerPropContext = map[string]string{}
var testClassNamedPropertyContext = map[string]string{}
var testClassTestClassNonShapeContext = map[string]string{}
var testClassTestClassNonnegativeIntegerPropContext = map[string]string{}
var testClassTestClassPositiveIntegerPropContext = map[string]string{}
var testClassTestClassRegexContext = map[string]string{}
var testClassTestClassRegexDatetimeContext = map[string]string{}
var testClassTestClassRegexDatetimestampContext = map[string]string{}
var testClassTestClassRegexListContext = map[string]string{}
var testClassTestClassStringListNoDatatypeContext = map[string]string{}
var testClassTestClassStringListPropContext = map[string]string{}
var testClassTestClassStringScalarPropContext = map[string]string{}

func DecodeTestClass (data any, path Path, context map[string]string) (Ref[TestClass], error) {
    return DecodeRef[TestClass](data, path, context, testClassType)
}

func (self TestClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestClass)
    _ = obj
    switch name {
    case "http://example.org/encode", "encode":
        val, err := DecodeString(value, path, testClassEncodeContext)
        if err != nil {
            return false, err
        }
        err = obj.Encode().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/import", "import":
        val, err := DecodeString(value, path, testClassImportContext)
        if err != nil {
            return false, err
        }
        err = obj.Import().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/anyuri-prop", "test-class/anyuri-prop":
        val, err := DecodeString(value, path, testClassTestClassAnyuriPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassAnyuriProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/boolean-prop", "test-class/boolean-prop":
        val, err := DecodeBoolean(value, path, testClassTestClassBooleanPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassBooleanProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-list-prop", "test-class/class-list-prop":
        val, err := DecodeList[Ref[TestClass]](value, path, testClassTestClassClassListPropContext, DecodeTestClass)
        if err != nil {
            return false, err
        }
        err = obj.TestClassClassListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-prop", "test-class/class-prop":
        val, err := DecodeTestClass(value, path, testClassTestClassClassPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassClassProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-prop-no-class", "test-class/class-prop-no-class":
        val, err := DecodeTestClass(value, path, testClassTestClassClassPropNoClassContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassClassPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetime-list-prop", "test-class/datetime-list-prop":
        val, err := DecodeList[time.Time](value, path, testClassTestClassDatetimeListPropContext, DecodeDateTime)
        if err != nil {
            return false, err
        }
        err = obj.TestClassDatetimeListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetime-scalar-prop", "test-class/datetime-scalar-prop":
        val, err := DecodeDateTime(value, path, testClassTestClassDatetimeScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassDatetimeScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetimestamp-scalar-prop", "test-class/datetimestamp-scalar-prop":
        val, err := DecodeDateTimeStamp(value, path, testClassTestClassDatetimestampScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassDatetimestampScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-list-prop", "test-class/enum-list-prop":
        val, err := DecodeList[string](value, path, testClassTestClassEnumListPropContext, DecodeIRI)
        if err != nil {
            return false, err
        }
        err = obj.TestClassEnumListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-prop", "test-class/enum-prop":
        val, err := DecodeIRI(value, path, testClassTestClassEnumPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassEnumProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-prop-no-class", "test-class/enum-prop-no-class":
        val, err := DecodeIRI(value, path, testClassTestClassEnumPropNoClassContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassEnumPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/float-prop", "test-class/float-prop":
        val, err := DecodeFloat(value, path, testClassTestClassFloatPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassFloatProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/integer-prop", "test-class/integer-prop":
        val, err := DecodeInteger(value, path, testClassTestClassIntegerPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/named-property", "test-class/named-property":
        val, err := DecodeString(value, path, testClassNamedPropertyContext)
        if err != nil {
            return false, err
        }
        err = obj.NamedProperty().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/non-shape", "test-class/non-shape":
        val, err := DecodeNonShapeClass(value, path, testClassTestClassNonShapeContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassNonShape().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/nonnegative-integer-prop", "test-class/nonnegative-integer-prop":
        val, err := DecodeInteger(value, path, testClassTestClassNonnegativeIntegerPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassNonnegativeIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/positive-integer-prop", "test-class/positive-integer-prop":
        val, err := DecodeInteger(value, path, testClassTestClassPositiveIntegerPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassPositiveIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex", "test-class/regex":
        val, err := DecodeString(value, path, testClassTestClassRegexContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegex().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-datetime", "test-class/regex-datetime":
        val, err := DecodeDateTime(value, path, testClassTestClassRegexDatetimeContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegexDatetime().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-datetimestamp", "test-class/regex-datetimestamp":
        val, err := DecodeDateTimeStamp(value, path, testClassTestClassRegexDatetimestampContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegexDatetimestamp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-list", "test-class/regex-list":
        val, err := DecodeList[string](value, path, testClassTestClassRegexListContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegexList().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-list-no-datatype", "test-class/string-list-no-datatype":
        val, err := DecodeList[string](value, path, testClassTestClassStringListNoDatatypeContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.TestClassStringListNoDatatype().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-list-prop", "test-class/string-list-prop":
        val, err := DecodeList[string](value, path, testClassTestClassStringListPropContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.TestClassStringListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-scalar-prop", "test-class/string-scalar-prop":
        val, err := DecodeString(value, path, testClassTestClassStringScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassStringScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self TestClassObjectType) Create() SHACLObject {
    return ConstructTestClassObject(&TestClassObject{})
}

func ConstructTestClassObject(o *TestClassObject) *TestClassObject {
    ConstructParentClassObject(&o.ParentClassObject)
    {
        validators := []Validator[string]{}
        o.encode = NewProperty[string]("encode", validators)
    }
    {
        validators := []Validator[string]{}
        o.import_ = NewProperty[string]("import_", validators)
    }
    {
        validators := []Validator[string]{}
        o.testClassAnyuriProp = NewProperty[string]("testClassAnyuriProp", validators)
    }
    {
        validators := []Validator[bool]{}
        o.testClassBooleanProp = NewProperty[bool]("testClassBooleanProp", validators)
    }
    {
        validators := []Validator[Ref[TestClass]]{}
        o.testClassClassListProp = NewRefListProperty[TestClass]("testClassClassListProp", validators)
    }
    {
        validators := []Validator[Ref[TestClass]]{}
        o.testClassClassProp = NewRefProperty[TestClass]("testClassClassProp", validators)
    }
    {
        validators := []Validator[Ref[TestClass]]{}
        o.testClassClassPropNoClass = NewRefProperty[TestClass]("testClassClassPropNoClass", validators)
    }
    {
        validators := []Validator[time.Time]{}
        o.testClassDatetimeListProp = NewListProperty[time.Time]("testClassDatetimeListProp", validators)
    }
    {
        validators := []Validator[time.Time]{}
        o.testClassDatetimeScalarProp = NewProperty[time.Time]("testClassDatetimeScalarProp", validators)
    }
    {
        validators := []Validator[time.Time]{}
        o.testClassDatetimestampScalarProp = NewProperty[time.Time]("testClassDatetimestampScalarProp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators,
            EnumValidator{[]string{
                "http://example.org/enumType/bar",
                "http://example.org/enumType/foo",
                "http://example.org/enumType/nolabel",
                "http://example.org/enumType/non-named-individual",
        }})
        o.testClassEnumListProp = NewListProperty[string]("testClassEnumListProp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators,
            EnumValidator{[]string{
                "http://example.org/enumType/bar",
                "http://example.org/enumType/foo",
                "http://example.org/enumType/nolabel",
                "http://example.org/enumType/non-named-individual",
        }})
        o.testClassEnumProp = NewProperty[string]("testClassEnumProp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators,
            EnumValidator{[]string{
                "http://example.org/enumType/bar",
                "http://example.org/enumType/foo",
                "http://example.org/enumType/nolabel",
                "http://example.org/enumType/non-named-individual",
        }})
        o.testClassEnumPropNoClass = NewProperty[string]("testClassEnumPropNoClass", validators)
    }
    {
        validators := []Validator[float64]{}
        o.testClassFloatProp = NewProperty[float64]("testClassFloatProp", validators)
    }
    {
        validators := []Validator[int]{}
        o.testClassIntegerProp = NewProperty[int]("testClassIntegerProp", validators)
    }
    {
        validators := []Validator[string]{}
        o.namedProperty = NewProperty[string]("namedProperty", validators)
    }
    {
        validators := []Validator[Ref[NonShapeClass]]{}
        o.testClassNonShape = NewRefProperty[NonShapeClass]("testClassNonShape", validators)
    }
    {
        validators := []Validator[int]{}
        validators = append(validators, IntegerMinValidator{0})
        o.testClassNonnegativeIntegerProp = NewProperty[int]("testClassNonnegativeIntegerProp", validators)
    }
    {
        validators := []Validator[int]{}
        validators = append(validators, IntegerMinValidator{1})
        o.testClassPositiveIntegerProp = NewProperty[int]("testClassPositiveIntegerProp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators, RegexValidator[string]{`^foo\d`})
        o.testClassRegex = NewProperty[string]("testClassRegex", validators)
    }
    {
        validators := []Validator[time.Time]{}
        validators = append(validators, RegexValidator[time.Time]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+01:00$`})
        o.testClassRegexDatetime = NewProperty[time.Time]("testClassRegexDatetime", validators)
    }
    {
        validators := []Validator[time.Time]{}
        validators = append(validators, RegexValidator[time.Time]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$`})
        o.testClassRegexDatetimestamp = NewProperty[time.Time]("testClassRegexDatetimestamp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators, RegexValidator[string]{`^foo\d`})
        o.testClassRegexList = NewListProperty[string]("testClassRegexList", validators)
    }
    {
        validators := []Validator[string]{}
        o.testClassStringListNoDatatype = NewListProperty[string]("testClassStringListNoDatatype", validators)
    }
    {
        validators := []Validator[string]{}
        o.testClassStringListProp = NewListProperty[string]("testClassStringListProp", validators)
    }
    {
        validators := []Validator[string]{}
        o.testClassStringScalarProp = NewProperty[string]("testClassStringScalarProp", validators)
    }
    return o
}

type TestClass interface {
    ParentClass
    Encode() PropertyInterface[string]
    Import() PropertyInterface[string]
    TestClassAnyuriProp() PropertyInterface[string]
    TestClassBooleanProp() PropertyInterface[bool]
    TestClassClassListProp() ListPropertyInterface[Ref[TestClass]]
    TestClassClassProp() RefPropertyInterface[TestClass]
    TestClassClassPropNoClass() RefPropertyInterface[TestClass]
    TestClassDatetimeListProp() ListPropertyInterface[time.Time]
    TestClassDatetimeScalarProp() PropertyInterface[time.Time]
    TestClassDatetimestampScalarProp() PropertyInterface[time.Time]
    TestClassEnumListProp() ListPropertyInterface[string]
    TestClassEnumProp() PropertyInterface[string]
    TestClassEnumPropNoClass() PropertyInterface[string]
    TestClassFloatProp() PropertyInterface[float64]
    TestClassIntegerProp() PropertyInterface[int]
    NamedProperty() PropertyInterface[string]
    TestClassNonShape() RefPropertyInterface[NonShapeClass]
    TestClassNonnegativeIntegerProp() PropertyInterface[int]
    TestClassPositiveIntegerProp() PropertyInterface[int]
    TestClassRegex() PropertyInterface[string]
    TestClassRegexDatetime() PropertyInterface[time.Time]
    TestClassRegexDatetimestamp() PropertyInterface[time.Time]
    TestClassRegexList() ListPropertyInterface[string]
    TestClassStringListNoDatatype() ListPropertyInterface[string]
    TestClassStringListProp() ListPropertyInterface[string]
    TestClassStringScalarProp() PropertyInterface[string]
}


func MakeTestClass() TestClass {
    return ConstructTestClassObject(&TestClassObject{})
}

func MakeTestClassRef() Ref[TestClass] {
    o := MakeTestClass()
    return MakeObjectRef[TestClass](o)
}

func (self *TestClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.ParentClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("encode")
        if ! self.encode.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("import_")
        if ! self.import_.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassAnyuriProp")
        if ! self.testClassAnyuriProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassBooleanProp")
        if ! self.testClassBooleanProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassClassListProp")
        if ! self.testClassClassListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassClassProp")
        if ! self.testClassClassProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassClassPropNoClass")
        if ! self.testClassClassPropNoClass.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassDatetimeListProp")
        if ! self.testClassDatetimeListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassDatetimeScalarProp")
        if ! self.testClassDatetimeScalarProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassDatetimestampScalarProp")
        if ! self.testClassDatetimestampScalarProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassEnumListProp")
        if ! self.testClassEnumListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassEnumProp")
        if ! self.testClassEnumProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassEnumPropNoClass")
        if ! self.testClassEnumPropNoClass.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassFloatProp")
        if ! self.testClassFloatProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassIntegerProp")
        if ! self.testClassIntegerProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("namedProperty")
        if ! self.namedProperty.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassNonShape")
        if ! self.testClassNonShape.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassNonnegativeIntegerProp")
        if ! self.testClassNonnegativeIntegerProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassPositiveIntegerProp")
        if ! self.testClassPositiveIntegerProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassRegex")
        if ! self.testClassRegex.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassRegexDatetime")
        if ! self.testClassRegexDatetime.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassRegexDatetimestamp")
        if ! self.testClassRegexDatetimestamp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassRegexList")
        if ! self.testClassRegexList.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassStringListNoDatatype")
        if ! self.testClassStringListNoDatatype.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassStringListProp")
        if ! self.testClassStringListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassStringScalarProp")
        if ! self.testClassStringScalarProp.Check(prop_path, handler) {
            valid = false
        }
    }
    return valid
}

func (self *TestClassObject) Walk(path Path, visit Visit) {
    self.ParentClassObject.Walk(path, visit)
    self.encode.Walk(path, visit)
    self.import_.Walk(path, visit)
    self.testClassAnyuriProp.Walk(path, visit)
    self.testClassBooleanProp.Walk(path, visit)
    self.testClassClassListProp.Walk(path, visit)
    self.testClassClassProp.Walk(path, visit)
    self.testClassClassPropNoClass.Walk(path, visit)
    self.testClassDatetimeListProp.Walk(path, visit)
    self.testClassDatetimeScalarProp.Walk(path, visit)
    self.testClassDatetimestampScalarProp.Walk(path, visit)
    self.testClassEnumListProp.Walk(path, visit)
    self.testClassEnumProp.Walk(path, visit)
    self.testClassEnumPropNoClass.Walk(path, visit)
    self.testClassFloatProp.Walk(path, visit)
    self.testClassIntegerProp.Walk(path, visit)
    self.namedProperty.Walk(path, visit)
    self.testClassNonShape.Walk(path, visit)
    self.testClassNonnegativeIntegerProp.Walk(path, visit)
    self.testClassPositiveIntegerProp.Walk(path, visit)
    self.testClassRegex.Walk(path, visit)
    self.testClassRegexDatetime.Walk(path, visit)
    self.testClassRegexDatetimestamp.Walk(path, visit)
    self.testClassRegexList.Walk(path, visit)
    self.testClassStringListNoDatatype.Walk(path, visit)
    self.testClassStringListProp.Walk(path, visit)
    self.testClassStringScalarProp.Walk(path, visit)
}


func (self *TestClassObject) Encode() PropertyInterface[string] { return &self.encode }
func (self *TestClassObject) Import() PropertyInterface[string] { return &self.import_ }
func (self *TestClassObject) TestClassAnyuriProp() PropertyInterface[string] { return &self.testClassAnyuriProp }
func (self *TestClassObject) TestClassBooleanProp() PropertyInterface[bool] { return &self.testClassBooleanProp }
func (self *TestClassObject) TestClassClassListProp() ListPropertyInterface[Ref[TestClass]] { return &self.testClassClassListProp }
func (self *TestClassObject) TestClassClassProp() RefPropertyInterface[TestClass] { return &self.testClassClassProp }
func (self *TestClassObject) TestClassClassPropNoClass() RefPropertyInterface[TestClass] { return &self.testClassClassPropNoClass }
func (self *TestClassObject) TestClassDatetimeListProp() ListPropertyInterface[time.Time] { return &self.testClassDatetimeListProp }
func (self *TestClassObject) TestClassDatetimeScalarProp() PropertyInterface[time.Time] { return &self.testClassDatetimeScalarProp }
func (self *TestClassObject) TestClassDatetimestampScalarProp() PropertyInterface[time.Time] { return &self.testClassDatetimestampScalarProp }
func (self *TestClassObject) TestClassEnumListProp() ListPropertyInterface[string] { return &self.testClassEnumListProp }
func (self *TestClassObject) TestClassEnumProp() PropertyInterface[string] { return &self.testClassEnumProp }
func (self *TestClassObject) TestClassEnumPropNoClass() PropertyInterface[string] { return &self.testClassEnumPropNoClass }
func (self *TestClassObject) TestClassFloatProp() PropertyInterface[float64] { return &self.testClassFloatProp }
func (self *TestClassObject) TestClassIntegerProp() PropertyInterface[int] { return &self.testClassIntegerProp }
func (self *TestClassObject) NamedProperty() PropertyInterface[string] { return &self.namedProperty }
func (self *TestClassObject) TestClassNonShape() RefPropertyInterface[NonShapeClass] { return &self.testClassNonShape }
func (self *TestClassObject) TestClassNonnegativeIntegerProp() PropertyInterface[int] { return &self.testClassNonnegativeIntegerProp }
func (self *TestClassObject) TestClassPositiveIntegerProp() PropertyInterface[int] { return &self.testClassPositiveIntegerProp }
func (self *TestClassObject) TestClassRegex() PropertyInterface[string] { return &self.testClassRegex }
func (self *TestClassObject) TestClassRegexDatetime() PropertyInterface[time.Time] { return &self.testClassRegexDatetime }
func (self *TestClassObject) TestClassRegexDatetimestamp() PropertyInterface[time.Time] { return &self.testClassRegexDatetimestamp }
func (self *TestClassObject) TestClassRegexList() ListPropertyInterface[string] { return &self.testClassRegexList }
func (self *TestClassObject) TestClassStringListNoDatatype() ListPropertyInterface[string] { return &self.testClassStringListNoDatatype }
func (self *TestClassObject) TestClassStringListProp() ListPropertyInterface[string] { return &self.testClassStringListProp }
func (self *TestClassObject) TestClassStringScalarProp() PropertyInterface[string] { return &self.testClassStringScalarProp }

func (self *TestClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.ParentClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.encode.IsSet() {
        data["encode"] = EncodeString(self.encode.Get(), path.PushPath("encode"), testClassEncodeContext)
    }
    if self.import_.IsSet() {
        data["import"] = EncodeString(self.import_.Get(), path.PushPath("import_"), testClassImportContext)
    }
    if self.testClassAnyuriProp.IsSet() {
        data["test-class/anyuri-prop"] = EncodeString(self.testClassAnyuriProp.Get(), path.PushPath("testClassAnyuriProp"), testClassTestClassAnyuriPropContext)
    }
    if self.testClassBooleanProp.IsSet() {
        data["test-class/boolean-prop"] = EncodeBoolean(self.testClassBooleanProp.Get(), path.PushPath("testClassBooleanProp"), testClassTestClassBooleanPropContext)
    }
    if self.testClassClassListProp.IsSet() {
        data["test-class/class-list-prop"] = EncodeList[Ref[TestClass]](self.testClassClassListProp.Get(), path.PushPath("testClassClassListProp"), testClassTestClassClassListPropContext, EncodeRef[TestClass])
    }
    if self.testClassClassProp.IsSet() {
        data["test-class/class-prop"] = EncodeRef[TestClass](self.testClassClassProp.Get(), path.PushPath("testClassClassProp"), testClassTestClassClassPropContext)
    }
    if self.testClassClassPropNoClass.IsSet() {
        data["test-class/class-prop-no-class"] = EncodeRef[TestClass](self.testClassClassPropNoClass.Get(), path.PushPath("testClassClassPropNoClass"), testClassTestClassClassPropNoClassContext)
    }
    if self.testClassDatetimeListProp.IsSet() {
        data["test-class/datetime-list-prop"] = EncodeList[time.Time](self.testClassDatetimeListProp.Get(), path.PushPath("testClassDatetimeListProp"), testClassTestClassDatetimeListPropContext, EncodeDateTime)
    }
    if self.testClassDatetimeScalarProp.IsSet() {
        data["test-class/datetime-scalar-prop"] = EncodeDateTime(self.testClassDatetimeScalarProp.Get(), path.PushPath("testClassDatetimeScalarProp"), testClassTestClassDatetimeScalarPropContext)
    }
    if self.testClassDatetimestampScalarProp.IsSet() {
        data["test-class/datetimestamp-scalar-prop"] = EncodeDateTime(self.testClassDatetimestampScalarProp.Get(), path.PushPath("testClassDatetimestampScalarProp"), testClassTestClassDatetimestampScalarPropContext)
    }
    if self.testClassEnumListProp.IsSet() {
        data["test-class/enum-list-prop"] = EncodeList[string](self.testClassEnumListProp.Get(), path.PushPath("testClassEnumListProp"), testClassTestClassEnumListPropContext, EncodeIRI)
    }
    if self.testClassEnumProp.IsSet() {
        data["test-class/enum-prop"] = EncodeIRI(self.testClassEnumProp.Get(), path.PushPath("testClassEnumProp"), testClassTestClassEnumPropContext)
    }
    if self.testClassEnumPropNoClass.IsSet() {
        data["test-class/enum-prop-no-class"] = EncodeIRI(self.testClassEnumPropNoClass.Get(), path.PushPath("testClassEnumPropNoClass"), testClassTestClassEnumPropNoClassContext)
    }
    if self.testClassFloatProp.IsSet() {
        data["test-class/float-prop"] = EncodeFloat(self.testClassFloatProp.Get(), path.PushPath("testClassFloatProp"), testClassTestClassFloatPropContext)
    }
    if self.testClassIntegerProp.IsSet() {
        data["test-class/integer-prop"] = EncodeInteger(self.testClassIntegerProp.Get(), path.PushPath("testClassIntegerProp"), testClassTestClassIntegerPropContext)
    }
    if self.namedProperty.IsSet() {
        data["test-class/named-property"] = EncodeString(self.namedProperty.Get(), path.PushPath("namedProperty"), testClassNamedPropertyContext)
    }
    if self.testClassNonShape.IsSet() {
        data["test-class/non-shape"] = EncodeRef[NonShapeClass](self.testClassNonShape.Get(), path.PushPath("testClassNonShape"), testClassTestClassNonShapeContext)
    }
    if self.testClassNonnegativeIntegerProp.IsSet() {
        data["test-class/nonnegative-integer-prop"] = EncodeInteger(self.testClassNonnegativeIntegerProp.Get(), path.PushPath("testClassNonnegativeIntegerProp"), testClassTestClassNonnegativeIntegerPropContext)
    }
    if self.testClassPositiveIntegerProp.IsSet() {
        data["test-class/positive-integer-prop"] = EncodeInteger(self.testClassPositiveIntegerProp.Get(), path.PushPath("testClassPositiveIntegerProp"), testClassTestClassPositiveIntegerPropContext)
    }
    if self.testClassRegex.IsSet() {
        data["test-class/regex"] = EncodeString(self.testClassRegex.Get(), path.PushPath("testClassRegex"), testClassTestClassRegexContext)
    }
    if self.testClassRegexDatetime.IsSet() {
        data["test-class/regex-datetime"] = EncodeDateTime(self.testClassRegexDatetime.Get(), path.PushPath("testClassRegexDatetime"), testClassTestClassRegexDatetimeContext)
    }
    if self.testClassRegexDatetimestamp.IsSet() {
        data["test-class/regex-datetimestamp"] = EncodeDateTime(self.testClassRegexDatetimestamp.Get(), path.PushPath("testClassRegexDatetimestamp"), testClassTestClassRegexDatetimestampContext)
    }
    if self.testClassRegexList.IsSet() {
        data["test-class/regex-list"] = EncodeList[string](self.testClassRegexList.Get(), path.PushPath("testClassRegexList"), testClassTestClassRegexListContext, EncodeString)
    }
    if self.testClassStringListNoDatatype.IsSet() {
        data["test-class/string-list-no-datatype"] = EncodeList[string](self.testClassStringListNoDatatype.Get(), path.PushPath("testClassStringListNoDatatype"), testClassTestClassStringListNoDatatypeContext, EncodeString)
    }
    if self.testClassStringListProp.IsSet() {
        data["test-class/string-list-prop"] = EncodeList[string](self.testClassStringListProp.Get(), path.PushPath("testClassStringListProp"), testClassTestClassStringListPropContext, EncodeString)
    }
    if self.testClassStringScalarProp.IsSet() {
        data["test-class/string-scalar-prop"] = EncodeString(self.testClassStringScalarProp.Get(), path.PushPath("testClassStringScalarProp"), testClassTestClassStringScalarPropContext)
    }
    return nil
}
type TestClassRequiredObject struct {
    TestClassObject

    // A required string list property
    testClassRequiredStringListProp ListProperty[string]
    // A required scalar string property
    testClassRequiredStringScalarProp Property[string]
}


type TestClassRequiredObjectType struct {
    SHACLTypeBase
}
var testClassRequiredType TestClassRequiredObjectType
var testClassRequiredTestClassRequiredStringListPropContext = map[string]string{}
var testClassRequiredTestClassRequiredStringScalarPropContext = map[string]string{}

func DecodeTestClassRequired (data any, path Path, context map[string]string) (Ref[TestClassRequired], error) {
    return DecodeRef[TestClassRequired](data, path, context, testClassRequiredType)
}

func (self TestClassRequiredObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestClassRequired)
    _ = obj
    switch name {
    case "http://example.org/test-class/required-string-list-prop", "test-class/required-string-list-prop":
        val, err := DecodeList[string](value, path, testClassRequiredTestClassRequiredStringListPropContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.TestClassRequiredStringListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/required-string-scalar-prop", "test-class/required-string-scalar-prop":
        val, err := DecodeString(value, path, testClassRequiredTestClassRequiredStringScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestClassRequiredStringScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self TestClassRequiredObjectType) Create() SHACLObject {
    return ConstructTestClassRequiredObject(&TestClassRequiredObject{})
}

func ConstructTestClassRequiredObject(o *TestClassRequiredObject) *TestClassRequiredObject {
    ConstructTestClassObject(&o.TestClassObject)
    {
        validators := []Validator[string]{}
        o.testClassRequiredStringListProp = NewListProperty[string]("testClassRequiredStringListProp", validators)
    }
    {
        validators := []Validator[string]{}
        o.testClassRequiredStringScalarProp = NewProperty[string]("testClassRequiredStringScalarProp", validators)
    }
    return o
}

type TestClassRequired interface {
    TestClass
    TestClassRequiredStringListProp() ListPropertyInterface[string]
    TestClassRequiredStringScalarProp() PropertyInterface[string]
}


func MakeTestClassRequired() TestClassRequired {
    return ConstructTestClassRequiredObject(&TestClassRequiredObject{})
}

func MakeTestClassRequiredRef() Ref[TestClassRequired] {
    o := MakeTestClassRequired()
    return MakeObjectRef[TestClassRequired](o)
}

func (self *TestClassRequiredObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.TestClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("testClassRequiredStringListProp")
        if ! self.testClassRequiredStringListProp.Check(prop_path, handler) {
            valid = false
        }
        if len(self.testClassRequiredStringListProp.Get()) < 1 {
            if handler != nil {
                handler.HandleError(&ValidationError{
                    "testClassRequiredStringListProp",
                    "Too few elements. Minimum of 1 required"},
                    prop_path)
            }
            valid = false
        }
        if len(self.testClassRequiredStringListProp.Get()) > 2 {
            if handler != nil {
                handler.HandleError(&ValidationError{
                    "testClassRequiredStringListProp",
                    "Too many elements. Maximum of 2 allowed"},
                    prop_path)
            }
            valid = false
        }
    }
    {
        prop_path := path.PushPath("testClassRequiredStringScalarProp")
        if ! self.testClassRequiredStringScalarProp.Check(prop_path, handler) {
            valid = false
        }
        if ! self.testClassRequiredStringScalarProp.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"testClassRequiredStringScalarProp", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *TestClassRequiredObject) Walk(path Path, visit Visit) {
    self.TestClassObject.Walk(path, visit)
    self.testClassRequiredStringListProp.Walk(path, visit)
    self.testClassRequiredStringScalarProp.Walk(path, visit)
}


func (self *TestClassRequiredObject) TestClassRequiredStringListProp() ListPropertyInterface[string] { return &self.testClassRequiredStringListProp }
func (self *TestClassRequiredObject) TestClassRequiredStringScalarProp() PropertyInterface[string] { return &self.testClassRequiredStringScalarProp }

func (self *TestClassRequiredObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.TestClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.testClassRequiredStringListProp.IsSet() {
        data["test-class/required-string-list-prop"] = EncodeList[string](self.testClassRequiredStringListProp.Get(), path.PushPath("testClassRequiredStringListProp"), testClassRequiredTestClassRequiredStringListPropContext, EncodeString)
    }
    if self.testClassRequiredStringScalarProp.IsSet() {
        data["test-class/required-string-scalar-prop"] = EncodeString(self.testClassRequiredStringScalarProp.Get(), path.PushPath("testClassRequiredStringScalarProp"), testClassRequiredTestClassRequiredStringScalarPropContext)
    }
    return nil
}

// A class derived from test-class
type TestDerivedClassObject struct {
    TestClassObject

    // A string property in a derived class
    testDerivedClassStringProp Property[string]
}


type TestDerivedClassObjectType struct {
    SHACLTypeBase
}
var testDerivedClassType TestDerivedClassObjectType
var testDerivedClassTestDerivedClassStringPropContext = map[string]string{}

func DecodeTestDerivedClass (data any, path Path, context map[string]string) (Ref[TestDerivedClass], error) {
    return DecodeRef[TestDerivedClass](data, path, context, testDerivedClassType)
}

func (self TestDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestDerivedClass)
    _ = obj
    switch name {
    case "http://example.org/test-derived-class/string-prop", "test-derived-class/string-prop":
        val, err := DecodeString(value, path, testDerivedClassTestDerivedClassStringPropContext)
        if err != nil {
            return false, err
        }
        err = obj.TestDerivedClassStringProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self TestDerivedClassObjectType) Create() SHACLObject {
    return ConstructTestDerivedClassObject(&TestDerivedClassObject{})
}

func ConstructTestDerivedClassObject(o *TestDerivedClassObject) *TestDerivedClassObject {
    ConstructTestClassObject(&o.TestClassObject)
    {
        validators := []Validator[string]{}
        o.testDerivedClassStringProp = NewProperty[string]("testDerivedClassStringProp", validators)
    }
    return o
}

type TestDerivedClass interface {
    TestClass
    TestDerivedClassStringProp() PropertyInterface[string]
}


func MakeTestDerivedClass() TestDerivedClass {
    return ConstructTestDerivedClassObject(&TestDerivedClassObject{})
}

func MakeTestDerivedClassRef() Ref[TestDerivedClass] {
    o := MakeTestDerivedClass()
    return MakeObjectRef[TestDerivedClass](o)
}

func (self *TestDerivedClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.TestClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("testDerivedClassStringProp")
        if ! self.testDerivedClassStringProp.Check(prop_path, handler) {
            valid = false
        }
    }
    return valid
}

func (self *TestDerivedClassObject) Walk(path Path, visit Visit) {
    self.TestClassObject.Walk(path, visit)
    self.testDerivedClassStringProp.Walk(path, visit)
}


func (self *TestDerivedClassObject) TestDerivedClassStringProp() PropertyInterface[string] { return &self.testDerivedClassStringProp }

func (self *TestDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.TestClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.testDerivedClassStringProp.IsSet() {
        data["test-derived-class/string-prop"] = EncodeString(self.testDerivedClassStringProp.Get(), path.PushPath("testDerivedClassStringProp"), testDerivedClassTestDerivedClassStringPropContext)
    }
    return nil
}

// A class that uses an abstract extensible class
type UsesExtensibleAbstractClassObject struct {
    SHACLObjectBase

    // A property that references and abstract extensible class
    usesExtensibleAbstractClassProp RefProperty[ExtensibleAbstractClass]
}


type UsesExtensibleAbstractClassObjectType struct {
    SHACLTypeBase
}
var usesExtensibleAbstractClassType UsesExtensibleAbstractClassObjectType
var usesExtensibleAbstractClassUsesExtensibleAbstractClassPropContext = map[string]string{}

func DecodeUsesExtensibleAbstractClass (data any, path Path, context map[string]string) (Ref[UsesExtensibleAbstractClass], error) {
    return DecodeRef[UsesExtensibleAbstractClass](data, path, context, usesExtensibleAbstractClassType)
}

func (self UsesExtensibleAbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(UsesExtensibleAbstractClass)
    _ = obj
    switch name {
    case "http://example.org/uses-extensible-abstract-class/prop", "uses-extensible-abstract-class/prop":
        val, err := DecodeExtensibleAbstractClass(value, path, usesExtensibleAbstractClassUsesExtensibleAbstractClassPropContext)
        if err != nil {
            return false, err
        }
        err = obj.UsesExtensibleAbstractClassProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self UsesExtensibleAbstractClassObjectType) Create() SHACLObject {
    return ConstructUsesExtensibleAbstractClassObject(&UsesExtensibleAbstractClassObject{})
}

func ConstructUsesExtensibleAbstractClassObject(o *UsesExtensibleAbstractClassObject) *UsesExtensibleAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    {
        validators := []Validator[Ref[ExtensibleAbstractClass]]{}
        o.usesExtensibleAbstractClassProp = NewRefProperty[ExtensibleAbstractClass]("usesExtensibleAbstractClassProp", validators)
    }
    return o
}

type UsesExtensibleAbstractClass interface {
    SHACLObject
    UsesExtensibleAbstractClassProp() RefPropertyInterface[ExtensibleAbstractClass]
}


func MakeUsesExtensibleAbstractClass() UsesExtensibleAbstractClass {
    return ConstructUsesExtensibleAbstractClassObject(&UsesExtensibleAbstractClassObject{})
}

func MakeUsesExtensibleAbstractClassRef() Ref[UsesExtensibleAbstractClass] {
    o := MakeUsesExtensibleAbstractClass()
    return MakeObjectRef[UsesExtensibleAbstractClass](o)
}

func (self *UsesExtensibleAbstractClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("usesExtensibleAbstractClassProp")
        if ! self.usesExtensibleAbstractClassProp.Check(prop_path, handler) {
            valid = false
        }
        if ! self.usesExtensibleAbstractClassProp.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"usesExtensibleAbstractClassProp", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *UsesExtensibleAbstractClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
    self.usesExtensibleAbstractClassProp.Walk(path, visit)
}


func (self *UsesExtensibleAbstractClassObject) UsesExtensibleAbstractClassProp() RefPropertyInterface[ExtensibleAbstractClass] { return &self.usesExtensibleAbstractClassProp }

func (self *UsesExtensibleAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.usesExtensibleAbstractClassProp.IsSet() {
        data["uses-extensible-abstract-class/prop"] = EncodeRef[ExtensibleAbstractClass](self.usesExtensibleAbstractClassProp.Get(), path.PushPath("usesExtensibleAbstractClassProp"), usesExtensibleAbstractClassUsesExtensibleAbstractClassPropContext)
    }
    return nil
}

// Derived class that sorts before the parent to test ordering
type AaaDerivedClassObject struct {
    ParentClassObject

}


type AaaDerivedClassObjectType struct {
    SHACLTypeBase
}
var aaaDerivedClassType AaaDerivedClassObjectType

func DecodeAaaDerivedClass (data any, path Path, context map[string]string) (Ref[AaaDerivedClass], error) {
    return DecodeRef[AaaDerivedClass](data, path, context, aaaDerivedClassType)
}

func (self AaaDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(AaaDerivedClass)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self AaaDerivedClassObjectType) Create() SHACLObject {
    return ConstructAaaDerivedClassObject(&AaaDerivedClassObject{})
}

func ConstructAaaDerivedClassObject(o *AaaDerivedClassObject) *AaaDerivedClassObject {
    ConstructParentClassObject(&o.ParentClassObject)
    return o
}

type AaaDerivedClass interface {
    ParentClass
}


func MakeAaaDerivedClass() AaaDerivedClass {
    return ConstructAaaDerivedClassObject(&AaaDerivedClassObject{})
}

func MakeAaaDerivedClassRef() Ref[AaaDerivedClass] {
    o := MakeAaaDerivedClass()
    return MakeObjectRef[AaaDerivedClass](o)
}

func (self *AaaDerivedClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.ParentClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *AaaDerivedClassObject) Walk(path Path, visit Visit) {
    self.ParentClassObject.Walk(path, visit)
}



func (self *AaaDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.ParentClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that derives its nodeKind from parent
type DerivedNodeKindIriObject struct {
    NodeKindIriObject

}


type DerivedNodeKindIriObjectType struct {
    SHACLTypeBase
}
var derivedNodeKindIriType DerivedNodeKindIriObjectType

func DecodeDerivedNodeKindIri (data any, path Path, context map[string]string) (Ref[DerivedNodeKindIri], error) {
    return DecodeRef[DerivedNodeKindIri](data, path, context, derivedNodeKindIriType)
}

func (self DerivedNodeKindIriObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(DerivedNodeKindIri)
    _ = obj
    switch name {
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self DerivedNodeKindIriObjectType) Create() SHACLObject {
    return ConstructDerivedNodeKindIriObject(&DerivedNodeKindIriObject{})
}

func ConstructDerivedNodeKindIriObject(o *DerivedNodeKindIriObject) *DerivedNodeKindIriObject {
    ConstructNodeKindIriObject(&o.NodeKindIriObject)
    return o
}

type DerivedNodeKindIri interface {
    NodeKindIri
}


func MakeDerivedNodeKindIri() DerivedNodeKindIri {
    return ConstructDerivedNodeKindIriObject(&DerivedNodeKindIriObject{})
}

func MakeDerivedNodeKindIriRef() Ref[DerivedNodeKindIri] {
    o := MakeDerivedNodeKindIri()
    return MakeObjectRef[DerivedNodeKindIri](o)
}

func (self *DerivedNodeKindIriObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.NodeKindIriObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *DerivedNodeKindIriObject) Walk(path Path, visit Visit) {
    self.NodeKindIriObject.Walk(path, visit)
}



func (self *DerivedNodeKindIriObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.NodeKindIriObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An extensible class
type ExtensibleClassObject struct {
    LinkClassObject
    SHACLExtensibleBase

    // An extensible property
    extensibleClassProperty Property[string]
    // A required extensible property
    extensibleClassRequired Property[string]
}


type ExtensibleClassObjectType struct {
    SHACLTypeBase
}
var extensibleClassType ExtensibleClassObjectType
var extensibleClassExtensibleClassPropertyContext = map[string]string{}
var extensibleClassExtensibleClassRequiredContext = map[string]string{}

func DecodeExtensibleClass (data any, path Path, context map[string]string) (Ref[ExtensibleClass], error) {
    return DecodeRef[ExtensibleClass](data, path, context, extensibleClassType)
}

func (self ExtensibleClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ExtensibleClass)
    _ = obj
    switch name {
    case "http://example.org/extensible-class/property", "extensible-class/property":
        val, err := DecodeString(value, path, extensibleClassExtensibleClassPropertyContext)
        if err != nil {
            return false, err
        }
        err = obj.ExtensibleClassProperty().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/extensible-class/required", "extensible-class/required":
        val, err := DecodeString(value, path, extensibleClassExtensibleClassRequiredContext)
        if err != nil {
            return false, err
        }
        err = obj.ExtensibleClassRequired().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    default:
        found, err := self.SHACLTypeBase.DecodeProperty(o, name, value, path)
        if err != nil || found {
            return found, err
        }
    }

    return false, nil
}

func (self ExtensibleClassObjectType) Create() SHACLObject {
    return ConstructExtensibleClassObject(&ExtensibleClassObject{})
}

func ConstructExtensibleClassObject(o *ExtensibleClassObject) *ExtensibleClassObject {
    ConstructLinkClassObject(&o.LinkClassObject)
    {
        validators := []Validator[string]{}
        o.extensibleClassProperty = NewProperty[string]("extensibleClassProperty", validators)
    }
    {
        validators := []Validator[string]{}
        o.extensibleClassRequired = NewProperty[string]("extensibleClassRequired", validators)
    }
    return o
}

type ExtensibleClass interface {
    LinkClass
    ExtensibleClassProperty() PropertyInterface[string]
    ExtensibleClassRequired() PropertyInterface[string]
}


func MakeExtensibleClass() ExtensibleClass {
    return ConstructExtensibleClassObject(&ExtensibleClassObject{})
}

func MakeExtensibleClassRef() Ref[ExtensibleClass] {
    o := MakeExtensibleClass()
    return MakeObjectRef[ExtensibleClass](o)
}

func (self *ExtensibleClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.LinkClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("extensibleClassProperty")
        if ! self.extensibleClassProperty.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("extensibleClassRequired")
        if ! self.extensibleClassRequired.Check(prop_path, handler) {
            valid = false
        }
        if ! self.extensibleClassRequired.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"extensibleClassRequired", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *ExtensibleClassObject) Walk(path Path, visit Visit) {
    self.LinkClassObject.Walk(path, visit)
    self.extensibleClassProperty.Walk(path, visit)
    self.extensibleClassRequired.Walk(path, visit)
}


func (self *ExtensibleClassObject) ExtensibleClassProperty() PropertyInterface[string] { return &self.extensibleClassProperty }
func (self *ExtensibleClassObject) ExtensibleClassRequired() PropertyInterface[string] { return &self.extensibleClassRequired }

func (self *ExtensibleClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.LinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.extensibleClassProperty.IsSet() {
        data["extensible-class/property"] = EncodeString(self.extensibleClassProperty.Get(), path.PushPath("extensibleClassProperty"), extensibleClassExtensibleClassPropertyContext)
    }
    if self.extensibleClassRequired.IsSet() {
        data["extensible-class/required"] = EncodeString(self.extensibleClassRequired.Get(), path.PushPath("extensibleClassRequired"), extensibleClassExtensibleClassRequiredContext)
    }
    self.SHACLExtensibleBase.EncodeExtProperties(data, path)
    return nil
}


func init() {
    objectTypes = make(map[string] SHACLType)
    abstractClassType = AbstractClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/abstract-class",
            compactTypeIRI: NewOptional[string]("abstract-class"),
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(abstractClassType)
    abstractShClassType = AbstractShClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/abstract-sh-class",
            compactTypeIRI: NewOptional[string]("abstract-sh-class"),
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(abstractShClassType)
    abstractSpdxClassType = AbstractSpdxClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/abstract-spdx-class",
            compactTypeIRI: NewOptional[string]("abstract-spdx-class"),
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(abstractSpdxClassType)
    concreteClassType = ConcreteClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/concrete-class",
            compactTypeIRI: NewOptional[string]("concrete-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/abstract-class",
            },
        },
    }
    RegisterType(concreteClassType)
    concreteShClassType = ConcreteShClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/concrete-sh-class",
            compactTypeIRI: NewOptional[string]("concrete-sh-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/abstract-sh-class",
            },
        },
    }
    RegisterType(concreteShClassType)
    concreteSpdxClassType = ConcreteSpdxClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/concrete-spdx-class",
            compactTypeIRI: NewOptional[string]("concrete-spdx-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/abstract-spdx-class",
            },
        },
    }
    RegisterType(concreteSpdxClassType)
    enumTypeType = EnumTypeObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/enumType",
            compactTypeIRI: NewOptional[string]("enumType"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(enumTypeType)
    extensibleAbstractClassType = ExtensibleAbstractClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/extensible-abstract-class",
            compactTypeIRI: NewOptional[string]("extensible-abstract-class"),
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            isExtensible: NewOptional[bool](true),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(extensibleAbstractClassType)
    idPropClassType = IdPropClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/id-prop-class",
            compactTypeIRI: NewOptional[string]("id-prop-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            idAlias: NewOptional[string]("testid"),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(idPropClassType)
    inheritedIdPropClassType = InheritedIdPropClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/inherited-id-prop-class",
            compactTypeIRI: NewOptional[string]("inherited-id-prop-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            idAlias: NewOptional[string]("testid"),
            parentIRIs: []string{
                "http://example.org/id-prop-class",
            },
        },
    }
    RegisterType(inheritedIdPropClassType)
    linkClassType = LinkClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/link-class",
            compactTypeIRI: NewOptional[string]("link-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(linkClassType)
    linkDerivedClassType = LinkDerivedClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/link-derived-class",
            compactTypeIRI: NewOptional[string]("link-derived-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(linkDerivedClassType)
    nodeKindBlankType = NodeKindBlankObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/node-kind-blank",
            compactTypeIRI: NewOptional[string]("node-kind-blank"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNode),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(nodeKindBlankType)
    nodeKindIriType = NodeKindIriObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/node-kind-iri",
            compactTypeIRI: NewOptional[string]("node-kind-iri"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindIRI),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(nodeKindIriType)
    nodeKindIriOrBlankType = NodeKindIriOrBlankObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/node-kind-iri-or-blank",
            compactTypeIRI: NewOptional[string]("node-kind-iri-or-blank"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(nodeKindIriOrBlankType)
    nonShapeClassType = NonShapeClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/non-shape-class",
            compactTypeIRI: NewOptional[string]("non-shape-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(nonShapeClassType)
    parentClassType = ParentClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/parent-class",
            compactTypeIRI: NewOptional[string]("parent-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(parentClassType)
    requiredAbstractType = RequiredAbstractObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/required-abstract",
            compactTypeIRI: NewOptional[string]("required-abstract"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(requiredAbstractType)
    testAnotherClassType = TestAnotherClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-another-class",
            compactTypeIRI: NewOptional[string]("test-another-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(testAnotherClassType)
    testClassType = TestClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-class",
            compactTypeIRI: NewOptional[string]("test-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/parent-class",
            },
        },
    }
    RegisterType(testClassType)
    testClassRequiredType = TestClassRequiredObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-class-required",
            compactTypeIRI: NewOptional[string]("test-class-required"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/test-class",
            },
        },
    }
    RegisterType(testClassRequiredType)
    testDerivedClassType = TestDerivedClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-derived-class",
            compactTypeIRI: NewOptional[string]("test-derived-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/test-class",
            },
        },
    }
    RegisterType(testDerivedClassType)
    usesExtensibleAbstractClassType = UsesExtensibleAbstractClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/uses-extensible-abstract-class",
            compactTypeIRI: NewOptional[string]("uses-extensible-abstract-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(usesExtensibleAbstractClassType)
    aaaDerivedClassType = AaaDerivedClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/aaa-derived-class",
            compactTypeIRI: NewOptional[string]("aaa-derived-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/parent-class",
            },
        },
    }
    RegisterType(aaaDerivedClassType)
    derivedNodeKindIriType = DerivedNodeKindIriObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/derived-node-kind-iri",
            compactTypeIRI: NewOptional[string]("derived-node-kind-iri"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindIRI),
            parentIRIs: []string{
                "http://example.org/node-kind-iri",
            },
        },
    }
    RegisterType(derivedNodeKindIriType)
    extensibleClassType = ExtensibleClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/extensible-class",
            compactTypeIRI: NewOptional[string]("extensible-class"),
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            isExtensible: NewOptional[bool](true),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(extensibleClassType)
}
