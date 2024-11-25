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
        if value != "" {
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
    data["@context"] = ""
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
type HttpExampleOrgAbstractClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgAbstractClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgAbstractClassType HttpExampleOrgAbstractClassObjectType

func DecodeHttpExampleOrgAbstractClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgAbstractClass], error) {
    return DecodeRef[HttpExampleOrgAbstractClass](data, path, context, httpExampleOrgAbstractClassType)
}

func (self HttpExampleOrgAbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgAbstractClass)
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

func (self HttpExampleOrgAbstractClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgAbstractClassObject(&HttpExampleOrgAbstractClassObject{})
}

func ConstructHttpExampleOrgAbstractClassObject(o *HttpExampleOrgAbstractClassObject) *HttpExampleOrgAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgAbstractClass interface {
    SHACLObject
}



func (self *HttpExampleOrgAbstractClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgAbstractClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}
type HttpExampleOrgAbstractShClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgAbstractShClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgAbstractShClassType HttpExampleOrgAbstractShClassObjectType

func DecodeHttpExampleOrgAbstractShClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgAbstractShClass], error) {
    return DecodeRef[HttpExampleOrgAbstractShClass](data, path, context, httpExampleOrgAbstractShClassType)
}

func (self HttpExampleOrgAbstractShClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgAbstractShClass)
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

func (self HttpExampleOrgAbstractShClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgAbstractShClassObject(&HttpExampleOrgAbstractShClassObject{})
}

func ConstructHttpExampleOrgAbstractShClassObject(o *HttpExampleOrgAbstractShClassObject) *HttpExampleOrgAbstractShClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgAbstractShClass interface {
    SHACLObject
}



func (self *HttpExampleOrgAbstractShClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgAbstractShClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgAbstractShClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An Abstract class using the SPDX type
type HttpExampleOrgAbstractSpdxClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgAbstractSpdxClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgAbstractSpdxClassType HttpExampleOrgAbstractSpdxClassObjectType

func DecodeHttpExampleOrgAbstractSpdxClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgAbstractSpdxClass], error) {
    return DecodeRef[HttpExampleOrgAbstractSpdxClass](data, path, context, httpExampleOrgAbstractSpdxClassType)
}

func (self HttpExampleOrgAbstractSpdxClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgAbstractSpdxClass)
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

func (self HttpExampleOrgAbstractSpdxClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgAbstractSpdxClassObject(&HttpExampleOrgAbstractSpdxClassObject{})
}

func ConstructHttpExampleOrgAbstractSpdxClassObject(o *HttpExampleOrgAbstractSpdxClassObject) *HttpExampleOrgAbstractSpdxClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgAbstractSpdxClass interface {
    SHACLObject
}



func (self *HttpExampleOrgAbstractSpdxClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgAbstractSpdxClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgAbstractSpdxClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A concrete class
type HttpExampleOrgConcreteClassObject struct {
    HttpExampleOrgAbstractClassObject

}


type HttpExampleOrgConcreteClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgConcreteClassType HttpExampleOrgConcreteClassObjectType

func DecodeHttpExampleOrgConcreteClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgConcreteClass], error) {
    return DecodeRef[HttpExampleOrgConcreteClass](data, path, context, httpExampleOrgConcreteClassType)
}

func (self HttpExampleOrgConcreteClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgConcreteClass)
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

func (self HttpExampleOrgConcreteClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgConcreteClassObject(&HttpExampleOrgConcreteClassObject{})
}

func ConstructHttpExampleOrgConcreteClassObject(o *HttpExampleOrgConcreteClassObject) *HttpExampleOrgConcreteClassObject {
    ConstructHttpExampleOrgAbstractClassObject(&o.HttpExampleOrgAbstractClassObject)
    return o
}

type HttpExampleOrgConcreteClass interface {
    HttpExampleOrgAbstractClass
}


func MakeHttpExampleOrgConcreteClass() HttpExampleOrgConcreteClass {
    return ConstructHttpExampleOrgConcreteClassObject(&HttpExampleOrgConcreteClassObject{})
}

func MakeHttpExampleOrgConcreteClassRef() Ref[HttpExampleOrgConcreteClass] {
    o := MakeHttpExampleOrgConcreteClass()
    return MakeObjectRef[HttpExampleOrgConcreteClass](o)
}

func (self *HttpExampleOrgConcreteClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgAbstractClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgConcreteClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgAbstractClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgConcreteClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgAbstractClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A concrete class
type HttpExampleOrgConcreteShClassObject struct {
    HttpExampleOrgAbstractShClassObject

}


type HttpExampleOrgConcreteShClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgConcreteShClassType HttpExampleOrgConcreteShClassObjectType

func DecodeHttpExampleOrgConcreteShClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgConcreteShClass], error) {
    return DecodeRef[HttpExampleOrgConcreteShClass](data, path, context, httpExampleOrgConcreteShClassType)
}

func (self HttpExampleOrgConcreteShClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgConcreteShClass)
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

func (self HttpExampleOrgConcreteShClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgConcreteShClassObject(&HttpExampleOrgConcreteShClassObject{})
}

func ConstructHttpExampleOrgConcreteShClassObject(o *HttpExampleOrgConcreteShClassObject) *HttpExampleOrgConcreteShClassObject {
    ConstructHttpExampleOrgAbstractShClassObject(&o.HttpExampleOrgAbstractShClassObject)
    return o
}

type HttpExampleOrgConcreteShClass interface {
    HttpExampleOrgAbstractShClass
}


func MakeHttpExampleOrgConcreteShClass() HttpExampleOrgConcreteShClass {
    return ConstructHttpExampleOrgConcreteShClassObject(&HttpExampleOrgConcreteShClassObject{})
}

func MakeHttpExampleOrgConcreteShClassRef() Ref[HttpExampleOrgConcreteShClass] {
    o := MakeHttpExampleOrgConcreteShClass()
    return MakeObjectRef[HttpExampleOrgConcreteShClass](o)
}

func (self *HttpExampleOrgConcreteShClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgAbstractShClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgConcreteShClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgAbstractShClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgConcreteShClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgAbstractShClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A concrete class
type HttpExampleOrgConcreteSpdxClassObject struct {
    HttpExampleOrgAbstractSpdxClassObject

}


type HttpExampleOrgConcreteSpdxClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgConcreteSpdxClassType HttpExampleOrgConcreteSpdxClassObjectType

func DecodeHttpExampleOrgConcreteSpdxClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgConcreteSpdxClass], error) {
    return DecodeRef[HttpExampleOrgConcreteSpdxClass](data, path, context, httpExampleOrgConcreteSpdxClassType)
}

func (self HttpExampleOrgConcreteSpdxClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgConcreteSpdxClass)
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

func (self HttpExampleOrgConcreteSpdxClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgConcreteSpdxClassObject(&HttpExampleOrgConcreteSpdxClassObject{})
}

func ConstructHttpExampleOrgConcreteSpdxClassObject(o *HttpExampleOrgConcreteSpdxClassObject) *HttpExampleOrgConcreteSpdxClassObject {
    ConstructHttpExampleOrgAbstractSpdxClassObject(&o.HttpExampleOrgAbstractSpdxClassObject)
    return o
}

type HttpExampleOrgConcreteSpdxClass interface {
    HttpExampleOrgAbstractSpdxClass
}


func MakeHttpExampleOrgConcreteSpdxClass() HttpExampleOrgConcreteSpdxClass {
    return ConstructHttpExampleOrgConcreteSpdxClassObject(&HttpExampleOrgConcreteSpdxClassObject{})
}

func MakeHttpExampleOrgConcreteSpdxClassRef() Ref[HttpExampleOrgConcreteSpdxClass] {
    o := MakeHttpExampleOrgConcreteSpdxClass()
    return MakeObjectRef[HttpExampleOrgConcreteSpdxClass](o)
}

func (self *HttpExampleOrgConcreteSpdxClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgAbstractSpdxClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgConcreteSpdxClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgAbstractSpdxClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgConcreteSpdxClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgAbstractSpdxClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An enumerated type
type HttpExampleOrgEnumTypeObject struct {
    SHACLObjectBase

}

// The foo value of enumType
const HttpExampleOrgEnumTypeFoo = "http://example.org/enumType/foo"
// The bar value of enumType
const HttpExampleOrgEnumTypeBar = "http://example.org/enumType/bar"
// This value has no label
const HttpExampleOrgEnumTypeNolabel = "http://example.org/enumType/nolabel"

type HttpExampleOrgEnumTypeObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgEnumTypeType HttpExampleOrgEnumTypeObjectType

func DecodeHttpExampleOrgEnumType (data any, path Path, context map[string]string) (Ref[HttpExampleOrgEnumType], error) {
    return DecodeRef[HttpExampleOrgEnumType](data, path, context, httpExampleOrgEnumTypeType)
}

func (self HttpExampleOrgEnumTypeObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgEnumType)
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

func (self HttpExampleOrgEnumTypeObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgEnumTypeObject(&HttpExampleOrgEnumTypeObject{})
}

func ConstructHttpExampleOrgEnumTypeObject(o *HttpExampleOrgEnumTypeObject) *HttpExampleOrgEnumTypeObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgEnumType interface {
    SHACLObject
}


func MakeHttpExampleOrgEnumType() HttpExampleOrgEnumType {
    return ConstructHttpExampleOrgEnumTypeObject(&HttpExampleOrgEnumTypeObject{})
}

func MakeHttpExampleOrgEnumTypeRef() Ref[HttpExampleOrgEnumType] {
    o := MakeHttpExampleOrgEnumType()
    return MakeObjectRef[HttpExampleOrgEnumType](o)
}

func (self *HttpExampleOrgEnumTypeObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgEnumTypeObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgEnumTypeObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An extensible abstract class
type HttpExampleOrgExtensibleAbstractClassObject struct {
    SHACLObjectBase
    SHACLExtensibleBase

}


type HttpExampleOrgExtensibleAbstractClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgExtensibleAbstractClassType HttpExampleOrgExtensibleAbstractClassObjectType

func DecodeHttpExampleOrgExtensibleAbstractClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgExtensibleAbstractClass], error) {
    return DecodeRef[HttpExampleOrgExtensibleAbstractClass](data, path, context, httpExampleOrgExtensibleAbstractClassType)
}

func (self HttpExampleOrgExtensibleAbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgExtensibleAbstractClass)
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

func (self HttpExampleOrgExtensibleAbstractClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgExtensibleAbstractClassObject(&HttpExampleOrgExtensibleAbstractClassObject{})
}

func ConstructHttpExampleOrgExtensibleAbstractClassObject(o *HttpExampleOrgExtensibleAbstractClassObject) *HttpExampleOrgExtensibleAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgExtensibleAbstractClass interface {
    SHACLObject
}



func (self *HttpExampleOrgExtensibleAbstractClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgExtensibleAbstractClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgExtensibleAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    self.SHACLExtensibleBase.EncodeExtProperties(data, path)
    return nil
}

// A class with an ID alias
type HttpExampleOrgIdPropClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgIdPropClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgIdPropClassType HttpExampleOrgIdPropClassObjectType

func DecodeHttpExampleOrgIdPropClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgIdPropClass], error) {
    return DecodeRef[HttpExampleOrgIdPropClass](data, path, context, httpExampleOrgIdPropClassType)
}

func (self HttpExampleOrgIdPropClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgIdPropClass)
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

func (self HttpExampleOrgIdPropClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgIdPropClassObject(&HttpExampleOrgIdPropClassObject{})
}

func ConstructHttpExampleOrgIdPropClassObject(o *HttpExampleOrgIdPropClassObject) *HttpExampleOrgIdPropClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgIdPropClass interface {
    SHACLObject
}


func MakeHttpExampleOrgIdPropClass() HttpExampleOrgIdPropClass {
    return ConstructHttpExampleOrgIdPropClassObject(&HttpExampleOrgIdPropClassObject{})
}

func MakeHttpExampleOrgIdPropClassRef() Ref[HttpExampleOrgIdPropClass] {
    o := MakeHttpExampleOrgIdPropClass()
    return MakeObjectRef[HttpExampleOrgIdPropClass](o)
}

func (self *HttpExampleOrgIdPropClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgIdPropClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgIdPropClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that inherits its idPropertyName from the parent
type HttpExampleOrgInheritedIdPropClassObject struct {
    HttpExampleOrgIdPropClassObject

}


type HttpExampleOrgInheritedIdPropClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgInheritedIdPropClassType HttpExampleOrgInheritedIdPropClassObjectType

func DecodeHttpExampleOrgInheritedIdPropClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgInheritedIdPropClass], error) {
    return DecodeRef[HttpExampleOrgInheritedIdPropClass](data, path, context, httpExampleOrgInheritedIdPropClassType)
}

func (self HttpExampleOrgInheritedIdPropClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgInheritedIdPropClass)
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

func (self HttpExampleOrgInheritedIdPropClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgInheritedIdPropClassObject(&HttpExampleOrgInheritedIdPropClassObject{})
}

func ConstructHttpExampleOrgInheritedIdPropClassObject(o *HttpExampleOrgInheritedIdPropClassObject) *HttpExampleOrgInheritedIdPropClassObject {
    ConstructHttpExampleOrgIdPropClassObject(&o.HttpExampleOrgIdPropClassObject)
    return o
}

type HttpExampleOrgInheritedIdPropClass interface {
    HttpExampleOrgIdPropClass
}


func MakeHttpExampleOrgInheritedIdPropClass() HttpExampleOrgInheritedIdPropClass {
    return ConstructHttpExampleOrgInheritedIdPropClassObject(&HttpExampleOrgInheritedIdPropClassObject{})
}

func MakeHttpExampleOrgInheritedIdPropClassRef() Ref[HttpExampleOrgInheritedIdPropClass] {
    o := MakeHttpExampleOrgInheritedIdPropClass()
    return MakeObjectRef[HttpExampleOrgInheritedIdPropClass](o)
}

func (self *HttpExampleOrgInheritedIdPropClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgIdPropClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgInheritedIdPropClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgIdPropClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgInheritedIdPropClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgIdPropClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class to test links
type HttpExampleOrgLinkClassObject struct {
    SHACLObjectBase

    // A link to an extensible-class
    extensible RefProperty[HttpExampleOrgExtensibleClass]
    // A link-class list property
    linkListProp RefListProperty[HttpExampleOrgLinkClass]
    // A link-class property
    linkProp RefProperty[HttpExampleOrgLinkClass]
    // A link-class property with no sh:class
    linkPropNoClass RefProperty[HttpExampleOrgLinkClass]
}


type HttpExampleOrgLinkClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgLinkClassType HttpExampleOrgLinkClassObjectType
var httpExampleOrgLinkClassExtensibleContext = map[string]string{}
var httpExampleOrgLinkClassLinkListPropContext = map[string]string{}
var httpExampleOrgLinkClassLinkPropContext = map[string]string{}
var httpExampleOrgLinkClassLinkPropNoClassContext = map[string]string{}

func DecodeHttpExampleOrgLinkClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgLinkClass], error) {
    return DecodeRef[HttpExampleOrgLinkClass](data, path, context, httpExampleOrgLinkClassType)
}

func (self HttpExampleOrgLinkClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgLinkClass)
    _ = obj
    switch name {
    case "http://example.org/link-class-extensible":
        val, err := DecodeHttpExampleOrgExtensibleClass(value, path, httpExampleOrgLinkClassExtensibleContext)
        if err != nil {
            return false, err
        }
        err = obj.Extensible().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-list-prop":
        val, err := DecodeList[Ref[HttpExampleOrgLinkClass]](value, path, httpExampleOrgLinkClassLinkListPropContext, DecodeHttpExampleOrgLinkClass)
        if err != nil {
            return false, err
        }
        err = obj.LinkListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-prop":
        val, err := DecodeHttpExampleOrgLinkClass(value, path, httpExampleOrgLinkClassLinkPropContext)
        if err != nil {
            return false, err
        }
        err = obj.LinkProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-prop-no-class":
        val, err := DecodeHttpExampleOrgLinkClass(value, path, httpExampleOrgLinkClassLinkPropNoClassContext)
        if err != nil {
            return false, err
        }
        err = obj.LinkPropNoClass().Set(val)
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

func (self HttpExampleOrgLinkClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgLinkClassObject(&HttpExampleOrgLinkClassObject{})
}

func ConstructHttpExampleOrgLinkClassObject(o *HttpExampleOrgLinkClassObject) *HttpExampleOrgLinkClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    {
        validators := []Validator[Ref[HttpExampleOrgExtensibleClass]]{}
        o.extensible = NewRefProperty[HttpExampleOrgExtensibleClass]("extensible", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgLinkClass]]{}
        o.linkListProp = NewRefListProperty[HttpExampleOrgLinkClass]("linkListProp", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgLinkClass]]{}
        o.linkProp = NewRefProperty[HttpExampleOrgLinkClass]("linkProp", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgLinkClass]]{}
        o.linkPropNoClass = NewRefProperty[HttpExampleOrgLinkClass]("linkPropNoClass", validators)
    }
    return o
}

type HttpExampleOrgLinkClass interface {
    SHACLObject
    Extensible() RefPropertyInterface[HttpExampleOrgExtensibleClass]
    LinkListProp() ListPropertyInterface[Ref[HttpExampleOrgLinkClass]]
    LinkProp() RefPropertyInterface[HttpExampleOrgLinkClass]
    LinkPropNoClass() RefPropertyInterface[HttpExampleOrgLinkClass]
}


func MakeHttpExampleOrgLinkClass() HttpExampleOrgLinkClass {
    return ConstructHttpExampleOrgLinkClassObject(&HttpExampleOrgLinkClassObject{})
}

func MakeHttpExampleOrgLinkClassRef() Ref[HttpExampleOrgLinkClass] {
    o := MakeHttpExampleOrgLinkClass()
    return MakeObjectRef[HttpExampleOrgLinkClass](o)
}

func (self *HttpExampleOrgLinkClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("extensible")
        if ! self.extensible.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("linkListProp")
        if ! self.linkListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("linkProp")
        if ! self.linkProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("linkPropNoClass")
        if ! self.linkPropNoClass.Check(prop_path, handler) {
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgLinkClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
    self.extensible.Walk(path, visit)
    self.linkListProp.Walk(path, visit)
    self.linkProp.Walk(path, visit)
    self.linkPropNoClass.Walk(path, visit)
}


func (self *HttpExampleOrgLinkClassObject) Extensible() RefPropertyInterface[HttpExampleOrgExtensibleClass] { return &self.extensible }
func (self *HttpExampleOrgLinkClassObject) LinkListProp() ListPropertyInterface[Ref[HttpExampleOrgLinkClass]] { return &self.linkListProp }
func (self *HttpExampleOrgLinkClassObject) LinkProp() RefPropertyInterface[HttpExampleOrgLinkClass] { return &self.linkProp }
func (self *HttpExampleOrgLinkClassObject) LinkPropNoClass() RefPropertyInterface[HttpExampleOrgLinkClass] { return &self.linkPropNoClass }

func (self *HttpExampleOrgLinkClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.extensible.IsSet() {
        data["http://example.org/link-class-extensible"] = EncodeRef[HttpExampleOrgExtensibleClass](self.extensible.Get(), path.PushPath("extensible"), httpExampleOrgLinkClassExtensibleContext)
    }
    if self.linkListProp.IsSet() {
        data["http://example.org/link-class-link-list-prop"] = EncodeList[Ref[HttpExampleOrgLinkClass]](self.linkListProp.Get(), path.PushPath("linkListProp"), httpExampleOrgLinkClassLinkListPropContext, EncodeRef[HttpExampleOrgLinkClass])
    }
    if self.linkProp.IsSet() {
        data["http://example.org/link-class-link-prop"] = EncodeRef[HttpExampleOrgLinkClass](self.linkProp.Get(), path.PushPath("linkProp"), httpExampleOrgLinkClassLinkPropContext)
    }
    if self.linkPropNoClass.IsSet() {
        data["http://example.org/link-class-link-prop-no-class"] = EncodeRef[HttpExampleOrgLinkClass](self.linkPropNoClass.Get(), path.PushPath("linkPropNoClass"), httpExampleOrgLinkClassLinkPropNoClassContext)
    }
    return nil
}

// A class derived from link-class
type HttpExampleOrgLinkDerivedClassObject struct {
    HttpExampleOrgLinkClassObject

}


type HttpExampleOrgLinkDerivedClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgLinkDerivedClassType HttpExampleOrgLinkDerivedClassObjectType

func DecodeHttpExampleOrgLinkDerivedClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgLinkDerivedClass], error) {
    return DecodeRef[HttpExampleOrgLinkDerivedClass](data, path, context, httpExampleOrgLinkDerivedClassType)
}

func (self HttpExampleOrgLinkDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgLinkDerivedClass)
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

func (self HttpExampleOrgLinkDerivedClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgLinkDerivedClassObject(&HttpExampleOrgLinkDerivedClassObject{})
}

func ConstructHttpExampleOrgLinkDerivedClassObject(o *HttpExampleOrgLinkDerivedClassObject) *HttpExampleOrgLinkDerivedClassObject {
    ConstructHttpExampleOrgLinkClassObject(&o.HttpExampleOrgLinkClassObject)
    return o
}

type HttpExampleOrgLinkDerivedClass interface {
    HttpExampleOrgLinkClass
}


func MakeHttpExampleOrgLinkDerivedClass() HttpExampleOrgLinkDerivedClass {
    return ConstructHttpExampleOrgLinkDerivedClassObject(&HttpExampleOrgLinkDerivedClassObject{})
}

func MakeHttpExampleOrgLinkDerivedClassRef() Ref[HttpExampleOrgLinkDerivedClass] {
    o := MakeHttpExampleOrgLinkDerivedClass()
    return MakeObjectRef[HttpExampleOrgLinkDerivedClass](o)
}

func (self *HttpExampleOrgLinkDerivedClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgLinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgLinkDerivedClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgLinkClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgLinkDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgLinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that must be a blank node
type HttpExampleOrgNodeKindBlankObject struct {
    HttpExampleOrgLinkClassObject

}


type HttpExampleOrgNodeKindBlankObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgNodeKindBlankType HttpExampleOrgNodeKindBlankObjectType

func DecodeHttpExampleOrgNodeKindBlank (data any, path Path, context map[string]string) (Ref[HttpExampleOrgNodeKindBlank], error) {
    return DecodeRef[HttpExampleOrgNodeKindBlank](data, path, context, httpExampleOrgNodeKindBlankType)
}

func (self HttpExampleOrgNodeKindBlankObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgNodeKindBlank)
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

func (self HttpExampleOrgNodeKindBlankObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgNodeKindBlankObject(&HttpExampleOrgNodeKindBlankObject{})
}

func ConstructHttpExampleOrgNodeKindBlankObject(o *HttpExampleOrgNodeKindBlankObject) *HttpExampleOrgNodeKindBlankObject {
    ConstructHttpExampleOrgLinkClassObject(&o.HttpExampleOrgLinkClassObject)
    return o
}

type HttpExampleOrgNodeKindBlank interface {
    HttpExampleOrgLinkClass
}


func MakeHttpExampleOrgNodeKindBlank() HttpExampleOrgNodeKindBlank {
    return ConstructHttpExampleOrgNodeKindBlankObject(&HttpExampleOrgNodeKindBlankObject{})
}

func MakeHttpExampleOrgNodeKindBlankRef() Ref[HttpExampleOrgNodeKindBlank] {
    o := MakeHttpExampleOrgNodeKindBlank()
    return MakeObjectRef[HttpExampleOrgNodeKindBlank](o)
}

func (self *HttpExampleOrgNodeKindBlankObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgLinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgNodeKindBlankObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgLinkClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgNodeKindBlankObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgLinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that must be an IRI
type HttpExampleOrgNodeKindIriObject struct {
    HttpExampleOrgLinkClassObject

}


type HttpExampleOrgNodeKindIriObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgNodeKindIriType HttpExampleOrgNodeKindIriObjectType

func DecodeHttpExampleOrgNodeKindIri (data any, path Path, context map[string]string) (Ref[HttpExampleOrgNodeKindIri], error) {
    return DecodeRef[HttpExampleOrgNodeKindIri](data, path, context, httpExampleOrgNodeKindIriType)
}

func (self HttpExampleOrgNodeKindIriObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgNodeKindIri)
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

func (self HttpExampleOrgNodeKindIriObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgNodeKindIriObject(&HttpExampleOrgNodeKindIriObject{})
}

func ConstructHttpExampleOrgNodeKindIriObject(o *HttpExampleOrgNodeKindIriObject) *HttpExampleOrgNodeKindIriObject {
    ConstructHttpExampleOrgLinkClassObject(&o.HttpExampleOrgLinkClassObject)
    return o
}

type HttpExampleOrgNodeKindIri interface {
    HttpExampleOrgLinkClass
}


func MakeHttpExampleOrgNodeKindIri() HttpExampleOrgNodeKindIri {
    return ConstructHttpExampleOrgNodeKindIriObject(&HttpExampleOrgNodeKindIriObject{})
}

func MakeHttpExampleOrgNodeKindIriRef() Ref[HttpExampleOrgNodeKindIri] {
    o := MakeHttpExampleOrgNodeKindIri()
    return MakeObjectRef[HttpExampleOrgNodeKindIri](o)
}

func (self *HttpExampleOrgNodeKindIriObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgLinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgNodeKindIriObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgLinkClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgNodeKindIriObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgLinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that can be either a blank node or an IRI
type HttpExampleOrgNodeKindIriOrBlankObject struct {
    HttpExampleOrgLinkClassObject

}


type HttpExampleOrgNodeKindIriOrBlankObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgNodeKindIriOrBlankType HttpExampleOrgNodeKindIriOrBlankObjectType

func DecodeHttpExampleOrgNodeKindIriOrBlank (data any, path Path, context map[string]string) (Ref[HttpExampleOrgNodeKindIriOrBlank], error) {
    return DecodeRef[HttpExampleOrgNodeKindIriOrBlank](data, path, context, httpExampleOrgNodeKindIriOrBlankType)
}

func (self HttpExampleOrgNodeKindIriOrBlankObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgNodeKindIriOrBlank)
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

func (self HttpExampleOrgNodeKindIriOrBlankObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgNodeKindIriOrBlankObject(&HttpExampleOrgNodeKindIriOrBlankObject{})
}

func ConstructHttpExampleOrgNodeKindIriOrBlankObject(o *HttpExampleOrgNodeKindIriOrBlankObject) *HttpExampleOrgNodeKindIriOrBlankObject {
    ConstructHttpExampleOrgLinkClassObject(&o.HttpExampleOrgLinkClassObject)
    return o
}

type HttpExampleOrgNodeKindIriOrBlank interface {
    HttpExampleOrgLinkClass
}


func MakeHttpExampleOrgNodeKindIriOrBlank() HttpExampleOrgNodeKindIriOrBlank {
    return ConstructHttpExampleOrgNodeKindIriOrBlankObject(&HttpExampleOrgNodeKindIriOrBlankObject{})
}

func MakeHttpExampleOrgNodeKindIriOrBlankRef() Ref[HttpExampleOrgNodeKindIriOrBlank] {
    o := MakeHttpExampleOrgNodeKindIriOrBlank()
    return MakeObjectRef[HttpExampleOrgNodeKindIriOrBlank](o)
}

func (self *HttpExampleOrgNodeKindIriOrBlankObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgLinkClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgNodeKindIriOrBlankObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgLinkClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgNodeKindIriOrBlankObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgLinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that is not a nodeshape
type HttpExampleOrgNonShapeClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgNonShapeClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgNonShapeClassType HttpExampleOrgNonShapeClassObjectType

func DecodeHttpExampleOrgNonShapeClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgNonShapeClass], error) {
    return DecodeRef[HttpExampleOrgNonShapeClass](data, path, context, httpExampleOrgNonShapeClassType)
}

func (self HttpExampleOrgNonShapeClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgNonShapeClass)
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

func (self HttpExampleOrgNonShapeClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgNonShapeClassObject(&HttpExampleOrgNonShapeClassObject{})
}

func ConstructHttpExampleOrgNonShapeClassObject(o *HttpExampleOrgNonShapeClassObject) *HttpExampleOrgNonShapeClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgNonShapeClass interface {
    SHACLObject
}


func MakeHttpExampleOrgNonShapeClass() HttpExampleOrgNonShapeClass {
    return ConstructHttpExampleOrgNonShapeClassObject(&HttpExampleOrgNonShapeClassObject{})
}

func MakeHttpExampleOrgNonShapeClassRef() Ref[HttpExampleOrgNonShapeClass] {
    o := MakeHttpExampleOrgNonShapeClass()
    return MakeObjectRef[HttpExampleOrgNonShapeClass](o)
}

func (self *HttpExampleOrgNonShapeClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgNonShapeClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgNonShapeClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// The parent class
type HttpExampleOrgParentClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgParentClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgParentClassType HttpExampleOrgParentClassObjectType

func DecodeHttpExampleOrgParentClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgParentClass], error) {
    return DecodeRef[HttpExampleOrgParentClass](data, path, context, httpExampleOrgParentClassType)
}

func (self HttpExampleOrgParentClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgParentClass)
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

func (self HttpExampleOrgParentClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgParentClassObject(&HttpExampleOrgParentClassObject{})
}

func ConstructHttpExampleOrgParentClassObject(o *HttpExampleOrgParentClassObject) *HttpExampleOrgParentClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgParentClass interface {
    SHACLObject
}


func MakeHttpExampleOrgParentClass() HttpExampleOrgParentClass {
    return ConstructHttpExampleOrgParentClassObject(&HttpExampleOrgParentClassObject{})
}

func MakeHttpExampleOrgParentClassRef() Ref[HttpExampleOrgParentClass] {
    o := MakeHttpExampleOrgParentClass()
    return MakeObjectRef[HttpExampleOrgParentClass](o)
}

func (self *HttpExampleOrgParentClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgParentClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgParentClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class with a mandatory abstract class
type HttpExampleOrgRequiredAbstractObject struct {
    SHACLObjectBase

    // A required abstract class property
    abstractClassProp RefProperty[HttpExampleOrgAbstractClass]
}


type HttpExampleOrgRequiredAbstractObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgRequiredAbstractType HttpExampleOrgRequiredAbstractObjectType
var httpExampleOrgRequiredAbstractAbstractClassPropContext = map[string]string{}

func DecodeHttpExampleOrgRequiredAbstract (data any, path Path, context map[string]string) (Ref[HttpExampleOrgRequiredAbstract], error) {
    return DecodeRef[HttpExampleOrgRequiredAbstract](data, path, context, httpExampleOrgRequiredAbstractType)
}

func (self HttpExampleOrgRequiredAbstractObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgRequiredAbstract)
    _ = obj
    switch name {
    case "http://example.org/required-abstract/abstract-class-prop":
        val, err := DecodeHttpExampleOrgAbstractClass(value, path, httpExampleOrgRequiredAbstractAbstractClassPropContext)
        if err != nil {
            return false, err
        }
        err = obj.AbstractClassProp().Set(val)
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

func (self HttpExampleOrgRequiredAbstractObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgRequiredAbstractObject(&HttpExampleOrgRequiredAbstractObject{})
}

func ConstructHttpExampleOrgRequiredAbstractObject(o *HttpExampleOrgRequiredAbstractObject) *HttpExampleOrgRequiredAbstractObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    {
        validators := []Validator[Ref[HttpExampleOrgAbstractClass]]{}
        o.abstractClassProp = NewRefProperty[HttpExampleOrgAbstractClass]("abstractClassProp", validators)
    }
    return o
}

type HttpExampleOrgRequiredAbstract interface {
    SHACLObject
    AbstractClassProp() RefPropertyInterface[HttpExampleOrgAbstractClass]
}


func MakeHttpExampleOrgRequiredAbstract() HttpExampleOrgRequiredAbstract {
    return ConstructHttpExampleOrgRequiredAbstractObject(&HttpExampleOrgRequiredAbstractObject{})
}

func MakeHttpExampleOrgRequiredAbstractRef() Ref[HttpExampleOrgRequiredAbstract] {
    o := MakeHttpExampleOrgRequiredAbstract()
    return MakeObjectRef[HttpExampleOrgRequiredAbstract](o)
}

func (self *HttpExampleOrgRequiredAbstractObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("abstractClassProp")
        if ! self.abstractClassProp.Check(prop_path, handler) {
            valid = false
        }
        if ! self.abstractClassProp.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"abstractClassProp", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgRequiredAbstractObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
    self.abstractClassProp.Walk(path, visit)
}


func (self *HttpExampleOrgRequiredAbstractObject) AbstractClassProp() RefPropertyInterface[HttpExampleOrgAbstractClass] { return &self.abstractClassProp }

func (self *HttpExampleOrgRequiredAbstractObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.abstractClassProp.IsSet() {
        data["http://example.org/required-abstract/abstract-class-prop"] = EncodeRef[HttpExampleOrgAbstractClass](self.abstractClassProp.Get(), path.PushPath("abstractClassProp"), httpExampleOrgRequiredAbstractAbstractClassPropContext)
    }
    return nil
}

// Another class
type HttpExampleOrgTestAnotherClassObject struct {
    SHACLObjectBase

}


type HttpExampleOrgTestAnotherClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgTestAnotherClassType HttpExampleOrgTestAnotherClassObjectType

func DecodeHttpExampleOrgTestAnotherClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgTestAnotherClass], error) {
    return DecodeRef[HttpExampleOrgTestAnotherClass](data, path, context, httpExampleOrgTestAnotherClassType)
}

func (self HttpExampleOrgTestAnotherClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgTestAnotherClass)
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

func (self HttpExampleOrgTestAnotherClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgTestAnotherClassObject(&HttpExampleOrgTestAnotherClassObject{})
}

func ConstructHttpExampleOrgTestAnotherClassObject(o *HttpExampleOrgTestAnotherClassObject) *HttpExampleOrgTestAnotherClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    return o
}

type HttpExampleOrgTestAnotherClass interface {
    SHACLObject
}


func MakeHttpExampleOrgTestAnotherClass() HttpExampleOrgTestAnotherClass {
    return ConstructHttpExampleOrgTestAnotherClassObject(&HttpExampleOrgTestAnotherClassObject{})
}

func MakeHttpExampleOrgTestAnotherClassRef() Ref[HttpExampleOrgTestAnotherClass] {
    o := MakeHttpExampleOrgTestAnotherClass()
    return MakeObjectRef[HttpExampleOrgTestAnotherClass](o)
}

func (self *HttpExampleOrgTestAnotherClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgTestAnotherClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
}



func (self *HttpExampleOrgTestAnotherClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// The test class
type HttpExampleOrgTestClassObject struct {
    HttpExampleOrgParentClassObject

    // A property that conflicts with an existing SHACLObject property
    encode Property[string]
    // A property that is a keyword
    import_ Property[string]
    // a URI
    anyuriProp Property[string]
    // a boolean property
    booleanProp Property[bool]
    // A test-class list property
    classListProp RefListProperty[HttpExampleOrgTestClass]
    // A test-class property
    classProp RefProperty[HttpExampleOrgTestClass]
    // A test-class property with no sh:class
    classPropNoClass RefProperty[HttpExampleOrgTestClass]
    // A datetime list property
    datetimeListProp ListProperty[time.Time]
    // A scalar datetime property
    datetimeScalarProp Property[time.Time]
    // A scalar dateTimeStamp property
    datetimestampScalarProp Property[time.Time]
    // A enum list property
    enumListProp ListProperty[string]
    // A enum property
    enumProp Property[string]
    // A enum property with no sh:class
    enumPropNoClass Property[string]
    // a float property
    floatProp Property[float64]
    // a non-negative integer
    integerProp Property[int]
    // A named property
    namedProperty Property[string]
    // A class with no shape
    nonShape RefProperty[HttpExampleOrgNonShapeClass]
    // a non-negative integer
    nonnegativeIntegerProp Property[int]
    // A positive integer
    positiveIntegerProp Property[int]
    // A regex validated string
    regex Property[string]
    // A regex dateTime
    regexDatetime Property[time.Time]
    // A regex dateTimeStamp
    regexDatetimestamp Property[time.Time]
    // A regex validated string list
    regexList ListProperty[string]
    // A string list property with no sh:datatype
    stringListNoDatatype ListProperty[string]
    // A string list property
    stringListProp ListProperty[string]
    // A scalar string propery
    stringScalarProp Property[string]
}
const HttpExampleOrgTestClassNamed = "http://example.org/test-class/named"

type HttpExampleOrgTestClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgTestClassType HttpExampleOrgTestClassObjectType
var httpExampleOrgTestClassEncodeContext = map[string]string{}
var httpExampleOrgTestClassImportContext = map[string]string{}
var httpExampleOrgTestClassAnyuriPropContext = map[string]string{}
var httpExampleOrgTestClassBooleanPropContext = map[string]string{}
var httpExampleOrgTestClassClassListPropContext = map[string]string{}
var httpExampleOrgTestClassClassPropContext = map[string]string{}
var httpExampleOrgTestClassClassPropNoClassContext = map[string]string{}
var httpExampleOrgTestClassDatetimeListPropContext = map[string]string{}
var httpExampleOrgTestClassDatetimeScalarPropContext = map[string]string{}
var httpExampleOrgTestClassDatetimestampScalarPropContext = map[string]string{}
var httpExampleOrgTestClassEnumListPropContext = map[string]string{
    "http://example.org/enumType/bar": "http://example.org/enumType/bar",
    "http://example.org/enumType/foo": "http://example.org/enumType/foo",
    "http://example.org/enumType/nolabel": "http://example.org/enumType/nolabel",
    "http://example.org/enumType/non-named-individual": "http://example.org/enumType/non-named-individual",}
var httpExampleOrgTestClassEnumPropContext = map[string]string{
    "http://example.org/enumType/bar": "http://example.org/enumType/bar",
    "http://example.org/enumType/foo": "http://example.org/enumType/foo",
    "http://example.org/enumType/nolabel": "http://example.org/enumType/nolabel",
    "http://example.org/enumType/non-named-individual": "http://example.org/enumType/non-named-individual",}
var httpExampleOrgTestClassEnumPropNoClassContext = map[string]string{
    "http://example.org/enumType/bar": "http://example.org/enumType/bar",
    "http://example.org/enumType/foo": "http://example.org/enumType/foo",
    "http://example.org/enumType/nolabel": "http://example.org/enumType/nolabel",
    "http://example.org/enumType/non-named-individual": "http://example.org/enumType/non-named-individual",}
var httpExampleOrgTestClassFloatPropContext = map[string]string{}
var httpExampleOrgTestClassIntegerPropContext = map[string]string{}
var httpExampleOrgTestClassNamedPropertyContext = map[string]string{}
var httpExampleOrgTestClassNonShapeContext = map[string]string{}
var httpExampleOrgTestClassNonnegativeIntegerPropContext = map[string]string{}
var httpExampleOrgTestClassPositiveIntegerPropContext = map[string]string{}
var httpExampleOrgTestClassRegexContext = map[string]string{}
var httpExampleOrgTestClassRegexDatetimeContext = map[string]string{}
var httpExampleOrgTestClassRegexDatetimestampContext = map[string]string{}
var httpExampleOrgTestClassRegexListContext = map[string]string{}
var httpExampleOrgTestClassStringListNoDatatypeContext = map[string]string{}
var httpExampleOrgTestClassStringListPropContext = map[string]string{}
var httpExampleOrgTestClassStringScalarPropContext = map[string]string{}

func DecodeHttpExampleOrgTestClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgTestClass], error) {
    return DecodeRef[HttpExampleOrgTestClass](data, path, context, httpExampleOrgTestClassType)
}

func (self HttpExampleOrgTestClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgTestClass)
    _ = obj
    switch name {
    case "http://example.org/encode":
        val, err := DecodeString(value, path, httpExampleOrgTestClassEncodeContext)
        if err != nil {
            return false, err
        }
        err = obj.Encode().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/import":
        val, err := DecodeString(value, path, httpExampleOrgTestClassImportContext)
        if err != nil {
            return false, err
        }
        err = obj.Import().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/anyuri-prop":
        val, err := DecodeString(value, path, httpExampleOrgTestClassAnyuriPropContext)
        if err != nil {
            return false, err
        }
        err = obj.AnyuriProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/boolean-prop":
        val, err := DecodeBoolean(value, path, httpExampleOrgTestClassBooleanPropContext)
        if err != nil {
            return false, err
        }
        err = obj.BooleanProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-list-prop":
        val, err := DecodeList[Ref[HttpExampleOrgTestClass]](value, path, httpExampleOrgTestClassClassListPropContext, DecodeHttpExampleOrgTestClass)
        if err != nil {
            return false, err
        }
        err = obj.ClassListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-prop":
        val, err := DecodeHttpExampleOrgTestClass(value, path, httpExampleOrgTestClassClassPropContext)
        if err != nil {
            return false, err
        }
        err = obj.ClassProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-prop-no-class":
        val, err := DecodeHttpExampleOrgTestClass(value, path, httpExampleOrgTestClassClassPropNoClassContext)
        if err != nil {
            return false, err
        }
        err = obj.ClassPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetime-list-prop":
        val, err := DecodeList[time.Time](value, path, httpExampleOrgTestClassDatetimeListPropContext, DecodeDateTime)
        if err != nil {
            return false, err
        }
        err = obj.DatetimeListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetime-scalar-prop":
        val, err := DecodeDateTime(value, path, httpExampleOrgTestClassDatetimeScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.DatetimeScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetimestamp-scalar-prop":
        val, err := DecodeDateTimeStamp(value, path, httpExampleOrgTestClassDatetimestampScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.DatetimestampScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-list-prop":
        val, err := DecodeList[string](value, path, httpExampleOrgTestClassEnumListPropContext, DecodeIRI)
        if err != nil {
            return false, err
        }
        err = obj.EnumListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-prop":
        val, err := DecodeIRI(value, path, httpExampleOrgTestClassEnumPropContext)
        if err != nil {
            return false, err
        }
        err = obj.EnumProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-prop-no-class":
        val, err := DecodeIRI(value, path, httpExampleOrgTestClassEnumPropNoClassContext)
        if err != nil {
            return false, err
        }
        err = obj.EnumPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/float-prop":
        val, err := DecodeFloat(value, path, httpExampleOrgTestClassFloatPropContext)
        if err != nil {
            return false, err
        }
        err = obj.FloatProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/integer-prop":
        val, err := DecodeInteger(value, path, httpExampleOrgTestClassIntegerPropContext)
        if err != nil {
            return false, err
        }
        err = obj.IntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/named-property":
        val, err := DecodeString(value, path, httpExampleOrgTestClassNamedPropertyContext)
        if err != nil {
            return false, err
        }
        err = obj.NamedProperty().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/non-shape":
        val, err := DecodeHttpExampleOrgNonShapeClass(value, path, httpExampleOrgTestClassNonShapeContext)
        if err != nil {
            return false, err
        }
        err = obj.NonShape().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/nonnegative-integer-prop":
        val, err := DecodeInteger(value, path, httpExampleOrgTestClassNonnegativeIntegerPropContext)
        if err != nil {
            return false, err
        }
        err = obj.NonnegativeIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/positive-integer-prop":
        val, err := DecodeInteger(value, path, httpExampleOrgTestClassPositiveIntegerPropContext)
        if err != nil {
            return false, err
        }
        err = obj.PositiveIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex":
        val, err := DecodeString(value, path, httpExampleOrgTestClassRegexContext)
        if err != nil {
            return false, err
        }
        err = obj.Regex().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-datetime":
        val, err := DecodeDateTime(value, path, httpExampleOrgTestClassRegexDatetimeContext)
        if err != nil {
            return false, err
        }
        err = obj.RegexDatetime().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-datetimestamp":
        val, err := DecodeDateTimeStamp(value, path, httpExampleOrgTestClassRegexDatetimestampContext)
        if err != nil {
            return false, err
        }
        err = obj.RegexDatetimestamp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-list":
        val, err := DecodeList[string](value, path, httpExampleOrgTestClassRegexListContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.RegexList().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-list-no-datatype":
        val, err := DecodeList[string](value, path, httpExampleOrgTestClassStringListNoDatatypeContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.StringListNoDatatype().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-list-prop":
        val, err := DecodeList[string](value, path, httpExampleOrgTestClassStringListPropContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.StringListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-scalar-prop":
        val, err := DecodeString(value, path, httpExampleOrgTestClassStringScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.StringScalarProp().Set(val)
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

func (self HttpExampleOrgTestClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgTestClassObject(&HttpExampleOrgTestClassObject{})
}

func ConstructHttpExampleOrgTestClassObject(o *HttpExampleOrgTestClassObject) *HttpExampleOrgTestClassObject {
    ConstructHttpExampleOrgParentClassObject(&o.HttpExampleOrgParentClassObject)
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
        o.anyuriProp = NewProperty[string]("anyuriProp", validators)
    }
    {
        validators := []Validator[bool]{}
        o.booleanProp = NewProperty[bool]("booleanProp", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgTestClass]]{}
        o.classListProp = NewRefListProperty[HttpExampleOrgTestClass]("classListProp", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgTestClass]]{}
        o.classProp = NewRefProperty[HttpExampleOrgTestClass]("classProp", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgTestClass]]{}
        o.classPropNoClass = NewRefProperty[HttpExampleOrgTestClass]("classPropNoClass", validators)
    }
    {
        validators := []Validator[time.Time]{}
        o.datetimeListProp = NewListProperty[time.Time]("datetimeListProp", validators)
    }
    {
        validators := []Validator[time.Time]{}
        o.datetimeScalarProp = NewProperty[time.Time]("datetimeScalarProp", validators)
    }
    {
        validators := []Validator[time.Time]{}
        o.datetimestampScalarProp = NewProperty[time.Time]("datetimestampScalarProp", validators)
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
        o.enumListProp = NewListProperty[string]("enumListProp", validators)
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
        o.enumProp = NewProperty[string]("enumProp", validators)
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
        o.enumPropNoClass = NewProperty[string]("enumPropNoClass", validators)
    }
    {
        validators := []Validator[float64]{}
        o.floatProp = NewProperty[float64]("floatProp", validators)
    }
    {
        validators := []Validator[int]{}
        o.integerProp = NewProperty[int]("integerProp", validators)
    }
    {
        validators := []Validator[string]{}
        o.namedProperty = NewProperty[string]("namedProperty", validators)
    }
    {
        validators := []Validator[Ref[HttpExampleOrgNonShapeClass]]{}
        o.nonShape = NewRefProperty[HttpExampleOrgNonShapeClass]("nonShape", validators)
    }
    {
        validators := []Validator[int]{}
        validators = append(validators, IntegerMinValidator{0})
        o.nonnegativeIntegerProp = NewProperty[int]("nonnegativeIntegerProp", validators)
    }
    {
        validators := []Validator[int]{}
        validators = append(validators, IntegerMinValidator{1})
        o.positiveIntegerProp = NewProperty[int]("positiveIntegerProp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators, RegexValidator[string]{`^foo\d`})
        o.regex = NewProperty[string]("regex", validators)
    }
    {
        validators := []Validator[time.Time]{}
        validators = append(validators, RegexValidator[time.Time]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+01:00$`})
        o.regexDatetime = NewProperty[time.Time]("regexDatetime", validators)
    }
    {
        validators := []Validator[time.Time]{}
        validators = append(validators, RegexValidator[time.Time]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$`})
        o.regexDatetimestamp = NewProperty[time.Time]("regexDatetimestamp", validators)
    }
    {
        validators := []Validator[string]{}
        validators = append(validators, RegexValidator[string]{`^foo\d`})
        o.regexList = NewListProperty[string]("regexList", validators)
    }
    {
        validators := []Validator[string]{}
        o.stringListNoDatatype = NewListProperty[string]("stringListNoDatatype", validators)
    }
    {
        validators := []Validator[string]{}
        o.stringListProp = NewListProperty[string]("stringListProp", validators)
    }
    {
        validators := []Validator[string]{}
        o.stringScalarProp = NewProperty[string]("stringScalarProp", validators)
    }
    return o
}

type HttpExampleOrgTestClass interface {
    HttpExampleOrgParentClass
    Encode() PropertyInterface[string]
    Import() PropertyInterface[string]
    AnyuriProp() PropertyInterface[string]
    BooleanProp() PropertyInterface[bool]
    ClassListProp() ListPropertyInterface[Ref[HttpExampleOrgTestClass]]
    ClassProp() RefPropertyInterface[HttpExampleOrgTestClass]
    ClassPropNoClass() RefPropertyInterface[HttpExampleOrgTestClass]
    DatetimeListProp() ListPropertyInterface[time.Time]
    DatetimeScalarProp() PropertyInterface[time.Time]
    DatetimestampScalarProp() PropertyInterface[time.Time]
    EnumListProp() ListPropertyInterface[string]
    EnumProp() PropertyInterface[string]
    EnumPropNoClass() PropertyInterface[string]
    FloatProp() PropertyInterface[float64]
    IntegerProp() PropertyInterface[int]
    NamedProperty() PropertyInterface[string]
    NonShape() RefPropertyInterface[HttpExampleOrgNonShapeClass]
    NonnegativeIntegerProp() PropertyInterface[int]
    PositiveIntegerProp() PropertyInterface[int]
    Regex() PropertyInterface[string]
    RegexDatetime() PropertyInterface[time.Time]
    RegexDatetimestamp() PropertyInterface[time.Time]
    RegexList() ListPropertyInterface[string]
    StringListNoDatatype() ListPropertyInterface[string]
    StringListProp() ListPropertyInterface[string]
    StringScalarProp() PropertyInterface[string]
}


func MakeHttpExampleOrgTestClass() HttpExampleOrgTestClass {
    return ConstructHttpExampleOrgTestClassObject(&HttpExampleOrgTestClassObject{})
}

func MakeHttpExampleOrgTestClassRef() Ref[HttpExampleOrgTestClass] {
    o := MakeHttpExampleOrgTestClass()
    return MakeObjectRef[HttpExampleOrgTestClass](o)
}

func (self *HttpExampleOrgTestClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgParentClassObject.Validate(path, handler) {
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
        prop_path := path.PushPath("anyuriProp")
        if ! self.anyuriProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("booleanProp")
        if ! self.booleanProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("classListProp")
        if ! self.classListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("classProp")
        if ! self.classProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("classPropNoClass")
        if ! self.classPropNoClass.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("datetimeListProp")
        if ! self.datetimeListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("datetimeScalarProp")
        if ! self.datetimeScalarProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("datetimestampScalarProp")
        if ! self.datetimestampScalarProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("enumListProp")
        if ! self.enumListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("enumProp")
        if ! self.enumProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("enumPropNoClass")
        if ! self.enumPropNoClass.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("floatProp")
        if ! self.floatProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("integerProp")
        if ! self.integerProp.Check(prop_path, handler) {
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
        prop_path := path.PushPath("nonShape")
        if ! self.nonShape.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("nonnegativeIntegerProp")
        if ! self.nonnegativeIntegerProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("positiveIntegerProp")
        if ! self.positiveIntegerProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("regex")
        if ! self.regex.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("regexDatetime")
        if ! self.regexDatetime.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("regexDatetimestamp")
        if ! self.regexDatetimestamp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("regexList")
        if ! self.regexList.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("stringListNoDatatype")
        if ! self.stringListNoDatatype.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("stringListProp")
        if ! self.stringListProp.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("stringScalarProp")
        if ! self.stringScalarProp.Check(prop_path, handler) {
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgTestClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgParentClassObject.Walk(path, visit)
    self.encode.Walk(path, visit)
    self.import_.Walk(path, visit)
    self.anyuriProp.Walk(path, visit)
    self.booleanProp.Walk(path, visit)
    self.classListProp.Walk(path, visit)
    self.classProp.Walk(path, visit)
    self.classPropNoClass.Walk(path, visit)
    self.datetimeListProp.Walk(path, visit)
    self.datetimeScalarProp.Walk(path, visit)
    self.datetimestampScalarProp.Walk(path, visit)
    self.enumListProp.Walk(path, visit)
    self.enumProp.Walk(path, visit)
    self.enumPropNoClass.Walk(path, visit)
    self.floatProp.Walk(path, visit)
    self.integerProp.Walk(path, visit)
    self.namedProperty.Walk(path, visit)
    self.nonShape.Walk(path, visit)
    self.nonnegativeIntegerProp.Walk(path, visit)
    self.positiveIntegerProp.Walk(path, visit)
    self.regex.Walk(path, visit)
    self.regexDatetime.Walk(path, visit)
    self.regexDatetimestamp.Walk(path, visit)
    self.regexList.Walk(path, visit)
    self.stringListNoDatatype.Walk(path, visit)
    self.stringListProp.Walk(path, visit)
    self.stringScalarProp.Walk(path, visit)
}


func (self *HttpExampleOrgTestClassObject) Encode() PropertyInterface[string] { return &self.encode }
func (self *HttpExampleOrgTestClassObject) Import() PropertyInterface[string] { return &self.import_ }
func (self *HttpExampleOrgTestClassObject) AnyuriProp() PropertyInterface[string] { return &self.anyuriProp }
func (self *HttpExampleOrgTestClassObject) BooleanProp() PropertyInterface[bool] { return &self.booleanProp }
func (self *HttpExampleOrgTestClassObject) ClassListProp() ListPropertyInterface[Ref[HttpExampleOrgTestClass]] { return &self.classListProp }
func (self *HttpExampleOrgTestClassObject) ClassProp() RefPropertyInterface[HttpExampleOrgTestClass] { return &self.classProp }
func (self *HttpExampleOrgTestClassObject) ClassPropNoClass() RefPropertyInterface[HttpExampleOrgTestClass] { return &self.classPropNoClass }
func (self *HttpExampleOrgTestClassObject) DatetimeListProp() ListPropertyInterface[time.Time] { return &self.datetimeListProp }
func (self *HttpExampleOrgTestClassObject) DatetimeScalarProp() PropertyInterface[time.Time] { return &self.datetimeScalarProp }
func (self *HttpExampleOrgTestClassObject) DatetimestampScalarProp() PropertyInterface[time.Time] { return &self.datetimestampScalarProp }
func (self *HttpExampleOrgTestClassObject) EnumListProp() ListPropertyInterface[string] { return &self.enumListProp }
func (self *HttpExampleOrgTestClassObject) EnumProp() PropertyInterface[string] { return &self.enumProp }
func (self *HttpExampleOrgTestClassObject) EnumPropNoClass() PropertyInterface[string] { return &self.enumPropNoClass }
func (self *HttpExampleOrgTestClassObject) FloatProp() PropertyInterface[float64] { return &self.floatProp }
func (self *HttpExampleOrgTestClassObject) IntegerProp() PropertyInterface[int] { return &self.integerProp }
func (self *HttpExampleOrgTestClassObject) NamedProperty() PropertyInterface[string] { return &self.namedProperty }
func (self *HttpExampleOrgTestClassObject) NonShape() RefPropertyInterface[HttpExampleOrgNonShapeClass] { return &self.nonShape }
func (self *HttpExampleOrgTestClassObject) NonnegativeIntegerProp() PropertyInterface[int] { return &self.nonnegativeIntegerProp }
func (self *HttpExampleOrgTestClassObject) PositiveIntegerProp() PropertyInterface[int] { return &self.positiveIntegerProp }
func (self *HttpExampleOrgTestClassObject) Regex() PropertyInterface[string] { return &self.regex }
func (self *HttpExampleOrgTestClassObject) RegexDatetime() PropertyInterface[time.Time] { return &self.regexDatetime }
func (self *HttpExampleOrgTestClassObject) RegexDatetimestamp() PropertyInterface[time.Time] { return &self.regexDatetimestamp }
func (self *HttpExampleOrgTestClassObject) RegexList() ListPropertyInterface[string] { return &self.regexList }
func (self *HttpExampleOrgTestClassObject) StringListNoDatatype() ListPropertyInterface[string] { return &self.stringListNoDatatype }
func (self *HttpExampleOrgTestClassObject) StringListProp() ListPropertyInterface[string] { return &self.stringListProp }
func (self *HttpExampleOrgTestClassObject) StringScalarProp() PropertyInterface[string] { return &self.stringScalarProp }

func (self *HttpExampleOrgTestClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgParentClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.encode.IsSet() {
        data["http://example.org/encode"] = EncodeString(self.encode.Get(), path.PushPath("encode"), httpExampleOrgTestClassEncodeContext)
    }
    if self.import_.IsSet() {
        data["http://example.org/import"] = EncodeString(self.import_.Get(), path.PushPath("import_"), httpExampleOrgTestClassImportContext)
    }
    if self.anyuriProp.IsSet() {
        data["http://example.org/test-class/anyuri-prop"] = EncodeString(self.anyuriProp.Get(), path.PushPath("anyuriProp"), httpExampleOrgTestClassAnyuriPropContext)
    }
    if self.booleanProp.IsSet() {
        data["http://example.org/test-class/boolean-prop"] = EncodeBoolean(self.booleanProp.Get(), path.PushPath("booleanProp"), httpExampleOrgTestClassBooleanPropContext)
    }
    if self.classListProp.IsSet() {
        data["http://example.org/test-class/class-list-prop"] = EncodeList[Ref[HttpExampleOrgTestClass]](self.classListProp.Get(), path.PushPath("classListProp"), httpExampleOrgTestClassClassListPropContext, EncodeRef[HttpExampleOrgTestClass])
    }
    if self.classProp.IsSet() {
        data["http://example.org/test-class/class-prop"] = EncodeRef[HttpExampleOrgTestClass](self.classProp.Get(), path.PushPath("classProp"), httpExampleOrgTestClassClassPropContext)
    }
    if self.classPropNoClass.IsSet() {
        data["http://example.org/test-class/class-prop-no-class"] = EncodeRef[HttpExampleOrgTestClass](self.classPropNoClass.Get(), path.PushPath("classPropNoClass"), httpExampleOrgTestClassClassPropNoClassContext)
    }
    if self.datetimeListProp.IsSet() {
        data["http://example.org/test-class/datetime-list-prop"] = EncodeList[time.Time](self.datetimeListProp.Get(), path.PushPath("datetimeListProp"), httpExampleOrgTestClassDatetimeListPropContext, EncodeDateTime)
    }
    if self.datetimeScalarProp.IsSet() {
        data["http://example.org/test-class/datetime-scalar-prop"] = EncodeDateTime(self.datetimeScalarProp.Get(), path.PushPath("datetimeScalarProp"), httpExampleOrgTestClassDatetimeScalarPropContext)
    }
    if self.datetimestampScalarProp.IsSet() {
        data["http://example.org/test-class/datetimestamp-scalar-prop"] = EncodeDateTime(self.datetimestampScalarProp.Get(), path.PushPath("datetimestampScalarProp"), httpExampleOrgTestClassDatetimestampScalarPropContext)
    }
    if self.enumListProp.IsSet() {
        data["http://example.org/test-class/enum-list-prop"] = EncodeList[string](self.enumListProp.Get(), path.PushPath("enumListProp"), httpExampleOrgTestClassEnumListPropContext, EncodeIRI)
    }
    if self.enumProp.IsSet() {
        data["http://example.org/test-class/enum-prop"] = EncodeIRI(self.enumProp.Get(), path.PushPath("enumProp"), httpExampleOrgTestClassEnumPropContext)
    }
    if self.enumPropNoClass.IsSet() {
        data["http://example.org/test-class/enum-prop-no-class"] = EncodeIRI(self.enumPropNoClass.Get(), path.PushPath("enumPropNoClass"), httpExampleOrgTestClassEnumPropNoClassContext)
    }
    if self.floatProp.IsSet() {
        data["http://example.org/test-class/float-prop"] = EncodeFloat(self.floatProp.Get(), path.PushPath("floatProp"), httpExampleOrgTestClassFloatPropContext)
    }
    if self.integerProp.IsSet() {
        data["http://example.org/test-class/integer-prop"] = EncodeInteger(self.integerProp.Get(), path.PushPath("integerProp"), httpExampleOrgTestClassIntegerPropContext)
    }
    if self.namedProperty.IsSet() {
        data["http://example.org/test-class/named-property"] = EncodeString(self.namedProperty.Get(), path.PushPath("namedProperty"), httpExampleOrgTestClassNamedPropertyContext)
    }
    if self.nonShape.IsSet() {
        data["http://example.org/test-class/non-shape"] = EncodeRef[HttpExampleOrgNonShapeClass](self.nonShape.Get(), path.PushPath("nonShape"), httpExampleOrgTestClassNonShapeContext)
    }
    if self.nonnegativeIntegerProp.IsSet() {
        data["http://example.org/test-class/nonnegative-integer-prop"] = EncodeInteger(self.nonnegativeIntegerProp.Get(), path.PushPath("nonnegativeIntegerProp"), httpExampleOrgTestClassNonnegativeIntegerPropContext)
    }
    if self.positiveIntegerProp.IsSet() {
        data["http://example.org/test-class/positive-integer-prop"] = EncodeInteger(self.positiveIntegerProp.Get(), path.PushPath("positiveIntegerProp"), httpExampleOrgTestClassPositiveIntegerPropContext)
    }
    if self.regex.IsSet() {
        data["http://example.org/test-class/regex"] = EncodeString(self.regex.Get(), path.PushPath("regex"), httpExampleOrgTestClassRegexContext)
    }
    if self.regexDatetime.IsSet() {
        data["http://example.org/test-class/regex-datetime"] = EncodeDateTime(self.regexDatetime.Get(), path.PushPath("regexDatetime"), httpExampleOrgTestClassRegexDatetimeContext)
    }
    if self.regexDatetimestamp.IsSet() {
        data["http://example.org/test-class/regex-datetimestamp"] = EncodeDateTime(self.regexDatetimestamp.Get(), path.PushPath("regexDatetimestamp"), httpExampleOrgTestClassRegexDatetimestampContext)
    }
    if self.regexList.IsSet() {
        data["http://example.org/test-class/regex-list"] = EncodeList[string](self.regexList.Get(), path.PushPath("regexList"), httpExampleOrgTestClassRegexListContext, EncodeString)
    }
    if self.stringListNoDatatype.IsSet() {
        data["http://example.org/test-class/string-list-no-datatype"] = EncodeList[string](self.stringListNoDatatype.Get(), path.PushPath("stringListNoDatatype"), httpExampleOrgTestClassStringListNoDatatypeContext, EncodeString)
    }
    if self.stringListProp.IsSet() {
        data["http://example.org/test-class/string-list-prop"] = EncodeList[string](self.stringListProp.Get(), path.PushPath("stringListProp"), httpExampleOrgTestClassStringListPropContext, EncodeString)
    }
    if self.stringScalarProp.IsSet() {
        data["http://example.org/test-class/string-scalar-prop"] = EncodeString(self.stringScalarProp.Get(), path.PushPath("stringScalarProp"), httpExampleOrgTestClassStringScalarPropContext)
    }
    return nil
}
type HttpExampleOrgTestClassRequiredObject struct {
    HttpExampleOrgTestClassObject

    // A required string list property
    requiredStringListProp ListProperty[string]
    // A required scalar string property
    requiredStringScalarProp Property[string]
}


type HttpExampleOrgTestClassRequiredObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgTestClassRequiredType HttpExampleOrgTestClassRequiredObjectType
var httpExampleOrgTestClassRequiredRequiredStringListPropContext = map[string]string{}
var httpExampleOrgTestClassRequiredRequiredStringScalarPropContext = map[string]string{}

func DecodeHttpExampleOrgTestClassRequired (data any, path Path, context map[string]string) (Ref[HttpExampleOrgTestClassRequired], error) {
    return DecodeRef[HttpExampleOrgTestClassRequired](data, path, context, httpExampleOrgTestClassRequiredType)
}

func (self HttpExampleOrgTestClassRequiredObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgTestClassRequired)
    _ = obj
    switch name {
    case "http://example.org/test-class/required-string-list-prop":
        val, err := DecodeList[string](value, path, httpExampleOrgTestClassRequiredRequiredStringListPropContext, DecodeString)
        if err != nil {
            return false, err
        }
        err = obj.RequiredStringListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/required-string-scalar-prop":
        val, err := DecodeString(value, path, httpExampleOrgTestClassRequiredRequiredStringScalarPropContext)
        if err != nil {
            return false, err
        }
        err = obj.RequiredStringScalarProp().Set(val)
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

func (self HttpExampleOrgTestClassRequiredObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgTestClassRequiredObject(&HttpExampleOrgTestClassRequiredObject{})
}

func ConstructHttpExampleOrgTestClassRequiredObject(o *HttpExampleOrgTestClassRequiredObject) *HttpExampleOrgTestClassRequiredObject {
    ConstructHttpExampleOrgTestClassObject(&o.HttpExampleOrgTestClassObject)
    {
        validators := []Validator[string]{}
        o.requiredStringListProp = NewListProperty[string]("requiredStringListProp", validators)
    }
    {
        validators := []Validator[string]{}
        o.requiredStringScalarProp = NewProperty[string]("requiredStringScalarProp", validators)
    }
    return o
}

type HttpExampleOrgTestClassRequired interface {
    HttpExampleOrgTestClass
    RequiredStringListProp() ListPropertyInterface[string]
    RequiredStringScalarProp() PropertyInterface[string]
}


func MakeHttpExampleOrgTestClassRequired() HttpExampleOrgTestClassRequired {
    return ConstructHttpExampleOrgTestClassRequiredObject(&HttpExampleOrgTestClassRequiredObject{})
}

func MakeHttpExampleOrgTestClassRequiredRef() Ref[HttpExampleOrgTestClassRequired] {
    o := MakeHttpExampleOrgTestClassRequired()
    return MakeObjectRef[HttpExampleOrgTestClassRequired](o)
}

func (self *HttpExampleOrgTestClassRequiredObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgTestClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("requiredStringListProp")
        if ! self.requiredStringListProp.Check(prop_path, handler) {
            valid = false
        }
        if len(self.requiredStringListProp.Get()) < 1 {
            if handler != nil {
                handler.HandleError(&ValidationError{
                    "requiredStringListProp",
                    "Too few elements. Minimum of 1 required"},
                    prop_path)
            }
            valid = false
        }
        if len(self.requiredStringListProp.Get()) > 2 {
            if handler != nil {
                handler.HandleError(&ValidationError{
                    "requiredStringListProp",
                    "Too many elements. Maximum of 2 allowed"},
                    prop_path)
            }
            valid = false
        }
    }
    {
        prop_path := path.PushPath("requiredStringScalarProp")
        if ! self.requiredStringScalarProp.Check(prop_path, handler) {
            valid = false
        }
        if ! self.requiredStringScalarProp.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"requiredStringScalarProp", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgTestClassRequiredObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgTestClassObject.Walk(path, visit)
    self.requiredStringListProp.Walk(path, visit)
    self.requiredStringScalarProp.Walk(path, visit)
}


func (self *HttpExampleOrgTestClassRequiredObject) RequiredStringListProp() ListPropertyInterface[string] { return &self.requiredStringListProp }
func (self *HttpExampleOrgTestClassRequiredObject) RequiredStringScalarProp() PropertyInterface[string] { return &self.requiredStringScalarProp }

func (self *HttpExampleOrgTestClassRequiredObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgTestClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.requiredStringListProp.IsSet() {
        data["http://example.org/test-class/required-string-list-prop"] = EncodeList[string](self.requiredStringListProp.Get(), path.PushPath("requiredStringListProp"), httpExampleOrgTestClassRequiredRequiredStringListPropContext, EncodeString)
    }
    if self.requiredStringScalarProp.IsSet() {
        data["http://example.org/test-class/required-string-scalar-prop"] = EncodeString(self.requiredStringScalarProp.Get(), path.PushPath("requiredStringScalarProp"), httpExampleOrgTestClassRequiredRequiredStringScalarPropContext)
    }
    return nil
}

// A class derived from test-class
type HttpExampleOrgTestDerivedClassObject struct {
    HttpExampleOrgTestClassObject

    // A string property in a derived class
    stringProp Property[string]
}


type HttpExampleOrgTestDerivedClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgTestDerivedClassType HttpExampleOrgTestDerivedClassObjectType
var httpExampleOrgTestDerivedClassStringPropContext = map[string]string{}

func DecodeHttpExampleOrgTestDerivedClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgTestDerivedClass], error) {
    return DecodeRef[HttpExampleOrgTestDerivedClass](data, path, context, httpExampleOrgTestDerivedClassType)
}

func (self HttpExampleOrgTestDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgTestDerivedClass)
    _ = obj
    switch name {
    case "http://example.org/test-derived-class/string-prop":
        val, err := DecodeString(value, path, httpExampleOrgTestDerivedClassStringPropContext)
        if err != nil {
            return false, err
        }
        err = obj.StringProp().Set(val)
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

func (self HttpExampleOrgTestDerivedClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgTestDerivedClassObject(&HttpExampleOrgTestDerivedClassObject{})
}

func ConstructHttpExampleOrgTestDerivedClassObject(o *HttpExampleOrgTestDerivedClassObject) *HttpExampleOrgTestDerivedClassObject {
    ConstructHttpExampleOrgTestClassObject(&o.HttpExampleOrgTestClassObject)
    {
        validators := []Validator[string]{}
        o.stringProp = NewProperty[string]("stringProp", validators)
    }
    return o
}

type HttpExampleOrgTestDerivedClass interface {
    HttpExampleOrgTestClass
    StringProp() PropertyInterface[string]
}


func MakeHttpExampleOrgTestDerivedClass() HttpExampleOrgTestDerivedClass {
    return ConstructHttpExampleOrgTestDerivedClassObject(&HttpExampleOrgTestDerivedClassObject{})
}

func MakeHttpExampleOrgTestDerivedClassRef() Ref[HttpExampleOrgTestDerivedClass] {
    o := MakeHttpExampleOrgTestDerivedClass()
    return MakeObjectRef[HttpExampleOrgTestDerivedClass](o)
}

func (self *HttpExampleOrgTestDerivedClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgTestClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("stringProp")
        if ! self.stringProp.Check(prop_path, handler) {
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgTestDerivedClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgTestClassObject.Walk(path, visit)
    self.stringProp.Walk(path, visit)
}


func (self *HttpExampleOrgTestDerivedClassObject) StringProp() PropertyInterface[string] { return &self.stringProp }

func (self *HttpExampleOrgTestDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgTestClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.stringProp.IsSet() {
        data["http://example.org/test-derived-class/string-prop"] = EncodeString(self.stringProp.Get(), path.PushPath("stringProp"), httpExampleOrgTestDerivedClassStringPropContext)
    }
    return nil
}

// A class that uses an abstract extensible class
type HttpExampleOrgUsesExtensibleAbstractClassObject struct {
    SHACLObjectBase

    // A property that references and abstract extensible class
    prop RefProperty[HttpExampleOrgExtensibleAbstractClass]
}


type HttpExampleOrgUsesExtensibleAbstractClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgUsesExtensibleAbstractClassType HttpExampleOrgUsesExtensibleAbstractClassObjectType
var httpExampleOrgUsesExtensibleAbstractClassPropContext = map[string]string{}

func DecodeHttpExampleOrgUsesExtensibleAbstractClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgUsesExtensibleAbstractClass], error) {
    return DecodeRef[HttpExampleOrgUsesExtensibleAbstractClass](data, path, context, httpExampleOrgUsesExtensibleAbstractClassType)
}

func (self HttpExampleOrgUsesExtensibleAbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgUsesExtensibleAbstractClass)
    _ = obj
    switch name {
    case "http://example.org/uses-extensible-abstract-class/prop":
        val, err := DecodeHttpExampleOrgExtensibleAbstractClass(value, path, httpExampleOrgUsesExtensibleAbstractClassPropContext)
        if err != nil {
            return false, err
        }
        err = obj.Prop().Set(val)
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

func (self HttpExampleOrgUsesExtensibleAbstractClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgUsesExtensibleAbstractClassObject(&HttpExampleOrgUsesExtensibleAbstractClassObject{})
}

func ConstructHttpExampleOrgUsesExtensibleAbstractClassObject(o *HttpExampleOrgUsesExtensibleAbstractClassObject) *HttpExampleOrgUsesExtensibleAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase)
    {
        validators := []Validator[Ref[HttpExampleOrgExtensibleAbstractClass]]{}
        o.prop = NewRefProperty[HttpExampleOrgExtensibleAbstractClass]("prop", validators)
    }
    return o
}

type HttpExampleOrgUsesExtensibleAbstractClass interface {
    SHACLObject
    Prop() RefPropertyInterface[HttpExampleOrgExtensibleAbstractClass]
}


func MakeHttpExampleOrgUsesExtensibleAbstractClass() HttpExampleOrgUsesExtensibleAbstractClass {
    return ConstructHttpExampleOrgUsesExtensibleAbstractClassObject(&HttpExampleOrgUsesExtensibleAbstractClassObject{})
}

func MakeHttpExampleOrgUsesExtensibleAbstractClassRef() Ref[HttpExampleOrgUsesExtensibleAbstractClass] {
    o := MakeHttpExampleOrgUsesExtensibleAbstractClass()
    return MakeObjectRef[HttpExampleOrgUsesExtensibleAbstractClass](o)
}

func (self *HttpExampleOrgUsesExtensibleAbstractClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.SHACLObjectBase.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("prop")
        if ! self.prop.Check(prop_path, handler) {
            valid = false
        }
        if ! self.prop.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"prop", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgUsesExtensibleAbstractClassObject) Walk(path Path, visit Visit) {
    self.SHACLObjectBase.Walk(path, visit)
    self.prop.Walk(path, visit)
}


func (self *HttpExampleOrgUsesExtensibleAbstractClassObject) Prop() RefPropertyInterface[HttpExampleOrgExtensibleAbstractClass] { return &self.prop }

func (self *HttpExampleOrgUsesExtensibleAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.prop.IsSet() {
        data["http://example.org/uses-extensible-abstract-class/prop"] = EncodeRef[HttpExampleOrgExtensibleAbstractClass](self.prop.Get(), path.PushPath("prop"), httpExampleOrgUsesExtensibleAbstractClassPropContext)
    }
    return nil
}

// Derived class that sorts before the parent to test ordering
type HttpExampleOrgAaaDerivedClassObject struct {
    HttpExampleOrgParentClassObject

}


type HttpExampleOrgAaaDerivedClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgAaaDerivedClassType HttpExampleOrgAaaDerivedClassObjectType

func DecodeHttpExampleOrgAaaDerivedClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgAaaDerivedClass], error) {
    return DecodeRef[HttpExampleOrgAaaDerivedClass](data, path, context, httpExampleOrgAaaDerivedClassType)
}

func (self HttpExampleOrgAaaDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgAaaDerivedClass)
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

func (self HttpExampleOrgAaaDerivedClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgAaaDerivedClassObject(&HttpExampleOrgAaaDerivedClassObject{})
}

func ConstructHttpExampleOrgAaaDerivedClassObject(o *HttpExampleOrgAaaDerivedClassObject) *HttpExampleOrgAaaDerivedClassObject {
    ConstructHttpExampleOrgParentClassObject(&o.HttpExampleOrgParentClassObject)
    return o
}

type HttpExampleOrgAaaDerivedClass interface {
    HttpExampleOrgParentClass
}


func MakeHttpExampleOrgAaaDerivedClass() HttpExampleOrgAaaDerivedClass {
    return ConstructHttpExampleOrgAaaDerivedClassObject(&HttpExampleOrgAaaDerivedClassObject{})
}

func MakeHttpExampleOrgAaaDerivedClassRef() Ref[HttpExampleOrgAaaDerivedClass] {
    o := MakeHttpExampleOrgAaaDerivedClass()
    return MakeObjectRef[HttpExampleOrgAaaDerivedClass](o)
}

func (self *HttpExampleOrgAaaDerivedClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgParentClassObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgAaaDerivedClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgParentClassObject.Walk(path, visit)
}



func (self *HttpExampleOrgAaaDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgParentClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// A class that derives its nodeKind from parent
type HttpExampleOrgDerivedNodeKindIriObject struct {
    HttpExampleOrgNodeKindIriObject

}


type HttpExampleOrgDerivedNodeKindIriObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgDerivedNodeKindIriType HttpExampleOrgDerivedNodeKindIriObjectType

func DecodeHttpExampleOrgDerivedNodeKindIri (data any, path Path, context map[string]string) (Ref[HttpExampleOrgDerivedNodeKindIri], error) {
    return DecodeRef[HttpExampleOrgDerivedNodeKindIri](data, path, context, httpExampleOrgDerivedNodeKindIriType)
}

func (self HttpExampleOrgDerivedNodeKindIriObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgDerivedNodeKindIri)
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

func (self HttpExampleOrgDerivedNodeKindIriObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgDerivedNodeKindIriObject(&HttpExampleOrgDerivedNodeKindIriObject{})
}

func ConstructHttpExampleOrgDerivedNodeKindIriObject(o *HttpExampleOrgDerivedNodeKindIriObject) *HttpExampleOrgDerivedNodeKindIriObject {
    ConstructHttpExampleOrgNodeKindIriObject(&o.HttpExampleOrgNodeKindIriObject)
    return o
}

type HttpExampleOrgDerivedNodeKindIri interface {
    HttpExampleOrgNodeKindIri
}


func MakeHttpExampleOrgDerivedNodeKindIri() HttpExampleOrgDerivedNodeKindIri {
    return ConstructHttpExampleOrgDerivedNodeKindIriObject(&HttpExampleOrgDerivedNodeKindIriObject{})
}

func MakeHttpExampleOrgDerivedNodeKindIriRef() Ref[HttpExampleOrgDerivedNodeKindIri] {
    o := MakeHttpExampleOrgDerivedNodeKindIri()
    return MakeObjectRef[HttpExampleOrgDerivedNodeKindIri](o)
}

func (self *HttpExampleOrgDerivedNodeKindIriObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgNodeKindIriObject.Validate(path, handler) {
        valid = false
    }
    return valid
}

func (self *HttpExampleOrgDerivedNodeKindIriObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgNodeKindIriObject.Walk(path, visit)
}



func (self *HttpExampleOrgDerivedNodeKindIriObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgNodeKindIriObject.EncodeProperties(data, path); err != nil {
        return err
    }
    return nil
}

// An extensible class
type HttpExampleOrgExtensibleClassObject struct {
    HttpExampleOrgLinkClassObject
    SHACLExtensibleBase

    // An extensible property
    property Property[string]
    // A required extensible property
    required Property[string]
}


type HttpExampleOrgExtensibleClassObjectType struct {
    SHACLTypeBase
}
var httpExampleOrgExtensibleClassType HttpExampleOrgExtensibleClassObjectType
var httpExampleOrgExtensibleClassPropertyContext = map[string]string{}
var httpExampleOrgExtensibleClassRequiredContext = map[string]string{}

func DecodeHttpExampleOrgExtensibleClass (data any, path Path, context map[string]string) (Ref[HttpExampleOrgExtensibleClass], error) {
    return DecodeRef[HttpExampleOrgExtensibleClass](data, path, context, httpExampleOrgExtensibleClassType)
}

func (self HttpExampleOrgExtensibleClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(HttpExampleOrgExtensibleClass)
    _ = obj
    switch name {
    case "http://example.org/extensible-class/property":
        val, err := DecodeString(value, path, httpExampleOrgExtensibleClassPropertyContext)
        if err != nil {
            return false, err
        }
        err = obj.Property().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/extensible-class/required":
        val, err := DecodeString(value, path, httpExampleOrgExtensibleClassRequiredContext)
        if err != nil {
            return false, err
        }
        err = obj.Required().Set(val)
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

func (self HttpExampleOrgExtensibleClassObjectType) Create() SHACLObject {
    return ConstructHttpExampleOrgExtensibleClassObject(&HttpExampleOrgExtensibleClassObject{})
}

func ConstructHttpExampleOrgExtensibleClassObject(o *HttpExampleOrgExtensibleClassObject) *HttpExampleOrgExtensibleClassObject {
    ConstructHttpExampleOrgLinkClassObject(&o.HttpExampleOrgLinkClassObject)
    {
        validators := []Validator[string]{}
        o.property = NewProperty[string]("property", validators)
    }
    {
        validators := []Validator[string]{}
        o.required = NewProperty[string]("required", validators)
    }
    return o
}

type HttpExampleOrgExtensibleClass interface {
    HttpExampleOrgLinkClass
    Property() PropertyInterface[string]
    Required() PropertyInterface[string]
}


func MakeHttpExampleOrgExtensibleClass() HttpExampleOrgExtensibleClass {
    return ConstructHttpExampleOrgExtensibleClassObject(&HttpExampleOrgExtensibleClassObject{})
}

func MakeHttpExampleOrgExtensibleClassRef() Ref[HttpExampleOrgExtensibleClass] {
    o := MakeHttpExampleOrgExtensibleClass()
    return MakeObjectRef[HttpExampleOrgExtensibleClass](o)
}

func (self *HttpExampleOrgExtensibleClassObject) Validate(path Path, handler ErrorHandler) bool {
    var valid bool = true
    if ! self.HttpExampleOrgLinkClassObject.Validate(path, handler) {
        valid = false
    }
    {
        prop_path := path.PushPath("property")
        if ! self.property.Check(prop_path, handler) {
            valid = false
        }
    }
    {
        prop_path := path.PushPath("required")
        if ! self.required.Check(prop_path, handler) {
            valid = false
        }
        if ! self.required.IsSet() {
            if handler != nil {
                handler.HandleError(&ValidationError{"required", "Value is required"}, prop_path)
            }
            valid = false
        }
    }
    return valid
}

func (self *HttpExampleOrgExtensibleClassObject) Walk(path Path, visit Visit) {
    self.HttpExampleOrgLinkClassObject.Walk(path, visit)
    self.property.Walk(path, visit)
    self.required.Walk(path, visit)
}


func (self *HttpExampleOrgExtensibleClassObject) Property() PropertyInterface[string] { return &self.property }
func (self *HttpExampleOrgExtensibleClassObject) Required() PropertyInterface[string] { return &self.required }

func (self *HttpExampleOrgExtensibleClassObject) EncodeProperties(data map[string]interface{}, path Path) error {
    if err := self.HttpExampleOrgLinkClassObject.EncodeProperties(data, path); err != nil {
        return err
    }
    if self.property.IsSet() {
        data["http://example.org/extensible-class/property"] = EncodeString(self.property.Get(), path.PushPath("property"), httpExampleOrgExtensibleClassPropertyContext)
    }
    if self.required.IsSet() {
        data["http://example.org/extensible-class/required"] = EncodeString(self.required.Get(), path.PushPath("required"), httpExampleOrgExtensibleClassRequiredContext)
    }
    self.SHACLExtensibleBase.EncodeExtProperties(data, path)
    return nil
}


func init() {
    objectTypes = make(map[string] SHACLType)
    httpExampleOrgAbstractClassType = HttpExampleOrgAbstractClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/abstract-class",
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgAbstractClassType)
    httpExampleOrgAbstractShClassType = HttpExampleOrgAbstractShClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/abstract-sh-class",
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgAbstractShClassType)
    httpExampleOrgAbstractSpdxClassType = HttpExampleOrgAbstractSpdxClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/abstract-spdx-class",
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgAbstractSpdxClassType)
    httpExampleOrgConcreteClassType = HttpExampleOrgConcreteClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/concrete-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/abstract-class",
            },
        },
    }
    RegisterType(httpExampleOrgConcreteClassType)
    httpExampleOrgConcreteShClassType = HttpExampleOrgConcreteShClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/concrete-sh-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/abstract-sh-class",
            },
        },
    }
    RegisterType(httpExampleOrgConcreteShClassType)
    httpExampleOrgConcreteSpdxClassType = HttpExampleOrgConcreteSpdxClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/concrete-spdx-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/abstract-spdx-class",
            },
        },
    }
    RegisterType(httpExampleOrgConcreteSpdxClassType)
    httpExampleOrgEnumTypeType = HttpExampleOrgEnumTypeObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/enumType",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgEnumTypeType)
    httpExampleOrgExtensibleAbstractClassType = HttpExampleOrgExtensibleAbstractClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/extensible-abstract-class",
            isAbstract: true,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            isExtensible: NewOptional[bool](true),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgExtensibleAbstractClassType)
    httpExampleOrgIdPropClassType = HttpExampleOrgIdPropClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/id-prop-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            idAlias: NewOptional[string]("testid"),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgIdPropClassType)
    httpExampleOrgInheritedIdPropClassType = HttpExampleOrgInheritedIdPropClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/inherited-id-prop-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            idAlias: NewOptional[string]("testid"),
            parentIRIs: []string{
                "http://example.org/id-prop-class",
            },
        },
    }
    RegisterType(httpExampleOrgInheritedIdPropClassType)
    httpExampleOrgLinkClassType = HttpExampleOrgLinkClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/link-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgLinkClassType)
    httpExampleOrgLinkDerivedClassType = HttpExampleOrgLinkDerivedClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/link-derived-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(httpExampleOrgLinkDerivedClassType)
    httpExampleOrgNodeKindBlankType = HttpExampleOrgNodeKindBlankObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/node-kind-blank",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNode),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(httpExampleOrgNodeKindBlankType)
    httpExampleOrgNodeKindIriType = HttpExampleOrgNodeKindIriObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/node-kind-iri",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindIRI),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(httpExampleOrgNodeKindIriType)
    httpExampleOrgNodeKindIriOrBlankType = HttpExampleOrgNodeKindIriOrBlankObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/node-kind-iri-or-blank",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(httpExampleOrgNodeKindIriOrBlankType)
    httpExampleOrgNonShapeClassType = HttpExampleOrgNonShapeClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/non-shape-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgNonShapeClassType)
    httpExampleOrgParentClassType = HttpExampleOrgParentClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/parent-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgParentClassType)
    httpExampleOrgRequiredAbstractType = HttpExampleOrgRequiredAbstractObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/required-abstract",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgRequiredAbstractType)
    httpExampleOrgTestAnotherClassType = HttpExampleOrgTestAnotherClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-another-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgTestAnotherClassType)
    httpExampleOrgTestClassType = HttpExampleOrgTestClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/parent-class",
            },
        },
    }
    RegisterType(httpExampleOrgTestClassType)
    httpExampleOrgTestClassRequiredType = HttpExampleOrgTestClassRequiredObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-class-required",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/test-class",
            },
        },
    }
    RegisterType(httpExampleOrgTestClassRequiredType)
    httpExampleOrgTestDerivedClassType = HttpExampleOrgTestDerivedClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/test-derived-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/test-class",
            },
        },
    }
    RegisterType(httpExampleOrgTestDerivedClassType)
    httpExampleOrgUsesExtensibleAbstractClassType = HttpExampleOrgUsesExtensibleAbstractClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/uses-extensible-abstract-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
            },
        },
    }
    RegisterType(httpExampleOrgUsesExtensibleAbstractClassType)
    httpExampleOrgAaaDerivedClassType = HttpExampleOrgAaaDerivedClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/aaa-derived-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            parentIRIs: []string{
                "http://example.org/parent-class",
            },
        },
    }
    RegisterType(httpExampleOrgAaaDerivedClassType)
    httpExampleOrgDerivedNodeKindIriType = HttpExampleOrgDerivedNodeKindIriObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/derived-node-kind-iri",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindIRI),
            parentIRIs: []string{
                "http://example.org/node-kind-iri",
            },
        },
    }
    RegisterType(httpExampleOrgDerivedNodeKindIriType)
    httpExampleOrgExtensibleClassType = HttpExampleOrgExtensibleClassObjectType{
        SHACLTypeBase: SHACLTypeBase{
            typeIRI: "http://example.org/extensible-class",
            isAbstract: false,
            nodeKind: NewOptional[int](NodeKindBlankNodeOrIRI),
            isExtensible: NewOptional[bool](true),
            parentIRIs: []string{
                "http://example.org/link-class",
            },
        },
    }
    RegisterType(httpExampleOrgExtensibleClassType)
}
