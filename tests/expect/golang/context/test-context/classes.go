//
//
//

package model

import (
    "time"
)


// An Abstract class
type AbstractClassObject struct {
    SHACLObjectBase

}


type AbstractClassObjectType struct {
    SHACLTypeBase
}
var abstractClassType AbstractClassObjectType

func DecodeAbstractClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[AbstractClass], error) {
    return DecodeRef[AbstractClass](data, path, context, abstractClassType, check)
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
    return ConstructAbstractClassObject(&AbstractClassObject{}, self)
}

func ConstructAbstractClassObject(o *AbstractClassObject, typ SHACLType) *AbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
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

func (self *AbstractClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *AbstractClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeAbstractShClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[AbstractShClass], error) {
    return DecodeRef[AbstractShClass](data, path, context, abstractShClassType, check)
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
    return ConstructAbstractShClassObject(&AbstractShClassObject{}, self)
}

func ConstructAbstractShClassObject(o *AbstractShClassObject, typ SHACLType) *AbstractShClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
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

func (self *AbstractShClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *AbstractShClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeAbstractSpdxClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[AbstractSpdxClass], error) {
    return DecodeRef[AbstractSpdxClass](data, path, context, abstractSpdxClassType, check)
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
    return ConstructAbstractSpdxClassObject(&AbstractSpdxClassObject{}, self)
}

func ConstructAbstractSpdxClassObject(o *AbstractSpdxClassObject, typ SHACLType) *AbstractSpdxClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
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

func (self *AbstractSpdxClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *AbstractSpdxClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeConcreteClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[ConcreteClass], error) {
    return DecodeRef[ConcreteClass](data, path, context, concreteClassType, check)
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
    return ConstructConcreteClassObject(&ConcreteClassObject{}, self)
}

func ConstructConcreteClassObject(o *ConcreteClassObject, typ SHACLType) *ConcreteClassObject {
    ConstructAbstractClassObject(&o.AbstractClassObject, typ)
    return o
}

type ConcreteClass interface {
    AbstractClass
}


func MakeConcreteClass() ConcreteClass {
    return ConstructConcreteClassObject(&ConcreteClassObject{}, concreteClassType)
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

func (self *ConcreteClassObject) Link(state *LinkState) error {
    if err := self.AbstractClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *ConcreteClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.AbstractClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeConcreteShClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[ConcreteShClass], error) {
    return DecodeRef[ConcreteShClass](data, path, context, concreteShClassType, check)
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
    return ConstructConcreteShClassObject(&ConcreteShClassObject{}, self)
}

func ConstructConcreteShClassObject(o *ConcreteShClassObject, typ SHACLType) *ConcreteShClassObject {
    ConstructAbstractShClassObject(&o.AbstractShClassObject, typ)
    return o
}

type ConcreteShClass interface {
    AbstractShClass
}


func MakeConcreteShClass() ConcreteShClass {
    return ConstructConcreteShClassObject(&ConcreteShClassObject{}, concreteShClassType)
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

func (self *ConcreteShClassObject) Link(state *LinkState) error {
    if err := self.AbstractShClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *ConcreteShClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.AbstractShClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeConcreteSpdxClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[ConcreteSpdxClass], error) {
    return DecodeRef[ConcreteSpdxClass](data, path, context, concreteSpdxClassType, check)
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
    return ConstructConcreteSpdxClassObject(&ConcreteSpdxClassObject{}, self)
}

func ConstructConcreteSpdxClassObject(o *ConcreteSpdxClassObject, typ SHACLType) *ConcreteSpdxClassObject {
    ConstructAbstractSpdxClassObject(&o.AbstractSpdxClassObject, typ)
    return o
}

type ConcreteSpdxClass interface {
    AbstractSpdxClass
}


func MakeConcreteSpdxClass() ConcreteSpdxClass {
    return ConstructConcreteSpdxClassObject(&ConcreteSpdxClassObject{}, concreteSpdxClassType)
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

func (self *ConcreteSpdxClassObject) Link(state *LinkState) error {
    if err := self.AbstractSpdxClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *ConcreteSpdxClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.AbstractSpdxClassObject.EncodeProperties(data, path, state); err != nil {
        return err
    }
    return nil
}

// An enumerated type
type EnumTypeObject struct {
    SHACLObjectBase

}

// The bar value of enumType
const EnumTypeBar = "http://example.org/enumType/bar"
// The foo value of enumType
const EnumTypeFoo = "http://example.org/enumType/foo"
// This value has no label
const EnumTypeNolabel = "http://example.org/enumType/nolabel"

type EnumTypeObjectType struct {
    SHACLTypeBase
}
var enumTypeType EnumTypeObjectType

func DecodeEnumType (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[EnumType], error) {
    return DecodeRef[EnumType](data, path, context, enumTypeType, check)
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
    return ConstructEnumTypeObject(&EnumTypeObject{}, self)
}

func ConstructEnumTypeObject(o *EnumTypeObject, typ SHACLType) *EnumTypeObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    return o
}

type EnumType interface {
    SHACLObject
}


func MakeEnumType() EnumType {
    return ConstructEnumTypeObject(&EnumTypeObject{}, enumTypeType)
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

func (self *EnumTypeObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *EnumTypeObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeExtensibleAbstractClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[ExtensibleAbstractClass], error) {
    return DecodeRef[ExtensibleAbstractClass](data, path, context, extensibleAbstractClassType, check)
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
    return ConstructExtensibleAbstractClassObject(&ExtensibleAbstractClassObject{}, self)
}

func ConstructExtensibleAbstractClassObject(o *ExtensibleAbstractClassObject, typ SHACLType) *ExtensibleAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
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

func (self *ExtensibleAbstractClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *ExtensibleAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeIdPropClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[IdPropClass], error) {
    return DecodeRef[IdPropClass](data, path, context, idPropClassType, check)
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
    return ConstructIdPropClassObject(&IdPropClassObject{}, self)
}

func ConstructIdPropClassObject(o *IdPropClassObject, typ SHACLType) *IdPropClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    return o
}

type IdPropClass interface {
    SHACLObject
}


func MakeIdPropClass() IdPropClass {
    return ConstructIdPropClassObject(&IdPropClassObject{}, idPropClassType)
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

func (self *IdPropClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *IdPropClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeInheritedIdPropClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[InheritedIdPropClass], error) {
    return DecodeRef[InheritedIdPropClass](data, path, context, inheritedIdPropClassType, check)
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
    return ConstructInheritedIdPropClassObject(&InheritedIdPropClassObject{}, self)
}

func ConstructInheritedIdPropClassObject(o *InheritedIdPropClassObject, typ SHACLType) *InheritedIdPropClassObject {
    ConstructIdPropClassObject(&o.IdPropClassObject, typ)
    return o
}

type InheritedIdPropClass interface {
    IdPropClass
}


func MakeInheritedIdPropClass() InheritedIdPropClass {
    return ConstructInheritedIdPropClassObject(&InheritedIdPropClassObject{}, inheritedIdPropClassType)
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

func (self *InheritedIdPropClassObject) Link(state *LinkState) error {
    if err := self.IdPropClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *InheritedIdPropClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.IdPropClassObject.EncodeProperties(data, path, state); err != nil {
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
    // Tag used to identify object for testing
    linkClassTag Property[string]
}


type LinkClassObjectType struct {
    SHACLTypeBase
}
var linkClassType LinkClassObjectType
var linkClassLinkClassExtensibleContext = map[string]string{}
var linkClassLinkClassLinkListPropContext = map[string]string{}
var linkClassLinkClassLinkPropContext = map[string]string{}
var linkClassLinkClassLinkPropNoClassContext = map[string]string{}
var linkClassLinkClassTagContext = map[string]string{}

func DecodeLinkClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[LinkClass], error) {
    return DecodeRef[LinkClass](data, path, context, linkClassType, check)
}

func (self LinkClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(LinkClass)
    _ = obj
    switch name {
    case "http://example.org/link-class-extensible", "link-class-extensible":
        val, err := DecodeExtensibleClass(value, path, linkClassLinkClassExtensibleContext, obj.LinkClassExtensible())
        if err != nil {
            return false, err
        }
        err = obj.LinkClassExtensible().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-list-prop", "link-class-link-list-prop":
        val, err := DecodeList[Ref[LinkClass]](value, path, linkClassLinkClassLinkListPropContext, DecodeLinkClass, obj.LinkClassLinkListProp())
        if err != nil {
            return false, err
        }
        err = obj.LinkClassLinkListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-prop", "link-class-link-prop":
        val, err := DecodeLinkClass(value, path, linkClassLinkClassLinkPropContext, obj.LinkClassLinkProp())
        if err != nil {
            return false, err
        }
        err = obj.LinkClassLinkProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-link-prop-no-class", "link-class-link-prop-no-class":
        val, err := DecodeLinkClass(value, path, linkClassLinkClassLinkPropNoClassContext, obj.LinkClassLinkPropNoClass())
        if err != nil {
            return false, err
        }
        err = obj.LinkClassLinkPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/link-class-tag", "link-class-tag":
        val, err := DecodeString(value, path, linkClassLinkClassTagContext, obj.LinkClassTag())
        if err != nil {
            return false, err
        }
        err = obj.LinkClassTag().Set(val)
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
    return ConstructLinkClassObject(&LinkClassObject{}, self)
}

func ConstructLinkClassObject(o *LinkClassObject, typ SHACLType) *LinkClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    {
        validators := []Validator[Ref[ExtensibleClass]]{}
        decodeValidators := []Validator[any]{}
        o.linkClassExtensible = NewRefProperty[ExtensibleClass]("linkClassExtensible", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[LinkClass]]{}
        decodeValidators := []Validator[any]{}
        o.linkClassLinkListProp = NewRefListProperty[LinkClass]("linkClassLinkListProp", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[LinkClass]]{}
        decodeValidators := []Validator[any]{}
        o.linkClassLinkProp = NewRefProperty[LinkClass]("linkClassLinkProp", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[LinkClass]]{}
        decodeValidators := []Validator[any]{}
        o.linkClassLinkPropNoClass = NewRefProperty[LinkClass]("linkClassLinkPropNoClass", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.linkClassTag = NewProperty[string]("linkClassTag", validators, decodeValidators)
    }
    return o
}

type LinkClass interface {
    SHACLObject
    LinkClassExtensible() RefPropertyInterface[ExtensibleClass]
    LinkClassLinkListProp() ListPropertyInterface[Ref[LinkClass]]
    LinkClassLinkProp() RefPropertyInterface[LinkClass]
    LinkClassLinkPropNoClass() RefPropertyInterface[LinkClass]
    LinkClassTag() PropertyInterface[string]
}


func MakeLinkClass() LinkClass {
    return ConstructLinkClassObject(&LinkClassObject{}, linkClassType)
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
    {
        prop_path := path.PushPath("linkClassTag")
        if ! self.linkClassTag.Check(prop_path, handler) {
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
    self.linkClassTag.Walk(path, visit)
}

func (self *LinkClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    if err := self.linkClassExtensible.Link(state); err != nil {
        return err
    }
    if err := self.linkClassLinkListProp.Link(state); err != nil {
        return err
    }
    if err := self.linkClassLinkProp.Link(state); err != nil {
        return err
    }
    if err := self.linkClassLinkPropNoClass.Link(state); err != nil {
        return err
    }
    if err := self.linkClassTag.Link(state); err != nil {
        return err
    }
    return nil
}


func (self *LinkClassObject) LinkClassExtensible() RefPropertyInterface[ExtensibleClass] { return &self.linkClassExtensible }
func (self *LinkClassObject) LinkClassLinkListProp() ListPropertyInterface[Ref[LinkClass]] { return &self.linkClassLinkListProp }
func (self *LinkClassObject) LinkClassLinkProp() RefPropertyInterface[LinkClass] { return &self.linkClassLinkProp }
func (self *LinkClassObject) LinkClassLinkPropNoClass() RefPropertyInterface[LinkClass] { return &self.linkClassLinkPropNoClass }
func (self *LinkClassObject) LinkClassTag() PropertyInterface[string] { return &self.linkClassTag }

func (self *LinkClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.linkClassExtensible.IsSet() {
        val, err := EncodeRef[ExtensibleClass](self.linkClassExtensible.Get(), path.PushPath("linkClassExtensible"), linkClassLinkClassExtensibleContext, state)
        if err != nil {
            return err
        }
        data["link-class-extensible"] = val
    }
    if self.linkClassLinkListProp.IsSet() {
        val, err := EncodeList[Ref[LinkClass]](self.linkClassLinkListProp.Get(), path.PushPath("linkClassLinkListProp"), linkClassLinkClassLinkListPropContext, state, EncodeRef[LinkClass])
        if err != nil {
            return err
        }
        data["link-class-link-list-prop"] = val
    }
    if self.linkClassLinkProp.IsSet() {
        val, err := EncodeRef[LinkClass](self.linkClassLinkProp.Get(), path.PushPath("linkClassLinkProp"), linkClassLinkClassLinkPropContext, state)
        if err != nil {
            return err
        }
        data["link-class-link-prop"] = val
    }
    if self.linkClassLinkPropNoClass.IsSet() {
        val, err := EncodeRef[LinkClass](self.linkClassLinkPropNoClass.Get(), path.PushPath("linkClassLinkPropNoClass"), linkClassLinkClassLinkPropNoClassContext, state)
        if err != nil {
            return err
        }
        data["link-class-link-prop-no-class"] = val
    }
    if self.linkClassTag.IsSet() {
        val, err := EncodeString(self.linkClassTag.Get(), path.PushPath("linkClassTag"), linkClassLinkClassTagContext, state)
        if err != nil {
            return err
        }
        data["link-class-tag"] = val
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

func DecodeLinkDerivedClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[LinkDerivedClass], error) {
    return DecodeRef[LinkDerivedClass](data, path, context, linkDerivedClassType, check)
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
    return ConstructLinkDerivedClassObject(&LinkDerivedClassObject{}, self)
}

func ConstructLinkDerivedClassObject(o *LinkDerivedClassObject, typ SHACLType) *LinkDerivedClassObject {
    ConstructLinkClassObject(&o.LinkClassObject, typ)
    return o
}

type LinkDerivedClass interface {
    LinkClass
}


func MakeLinkDerivedClass() LinkDerivedClass {
    return ConstructLinkDerivedClassObject(&LinkDerivedClassObject{}, linkDerivedClassType)
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

func (self *LinkDerivedClassObject) Link(state *LinkState) error {
    if err := self.LinkClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *LinkDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.LinkClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeNodeKindBlank (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[NodeKindBlank], error) {
    return DecodeRef[NodeKindBlank](data, path, context, nodeKindBlankType, check)
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
    return ConstructNodeKindBlankObject(&NodeKindBlankObject{}, self)
}

func ConstructNodeKindBlankObject(o *NodeKindBlankObject, typ SHACLType) *NodeKindBlankObject {
    ConstructLinkClassObject(&o.LinkClassObject, typ)
    return o
}

type NodeKindBlank interface {
    LinkClass
}


func MakeNodeKindBlank() NodeKindBlank {
    return ConstructNodeKindBlankObject(&NodeKindBlankObject{}, nodeKindBlankType)
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

func (self *NodeKindBlankObject) Link(state *LinkState) error {
    if err := self.LinkClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *NodeKindBlankObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.LinkClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeNodeKindIri (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[NodeKindIri], error) {
    return DecodeRef[NodeKindIri](data, path, context, nodeKindIriType, check)
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
    return ConstructNodeKindIriObject(&NodeKindIriObject{}, self)
}

func ConstructNodeKindIriObject(o *NodeKindIriObject, typ SHACLType) *NodeKindIriObject {
    ConstructLinkClassObject(&o.LinkClassObject, typ)
    return o
}

type NodeKindIri interface {
    LinkClass
}


func MakeNodeKindIri() NodeKindIri {
    return ConstructNodeKindIriObject(&NodeKindIriObject{}, nodeKindIriType)
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

func (self *NodeKindIriObject) Link(state *LinkState) error {
    if err := self.LinkClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *NodeKindIriObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.LinkClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeNodeKindIriOrBlank (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[NodeKindIriOrBlank], error) {
    return DecodeRef[NodeKindIriOrBlank](data, path, context, nodeKindIriOrBlankType, check)
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
    return ConstructNodeKindIriOrBlankObject(&NodeKindIriOrBlankObject{}, self)
}

func ConstructNodeKindIriOrBlankObject(o *NodeKindIriOrBlankObject, typ SHACLType) *NodeKindIriOrBlankObject {
    ConstructLinkClassObject(&o.LinkClassObject, typ)
    return o
}

type NodeKindIriOrBlank interface {
    LinkClass
}


func MakeNodeKindIriOrBlank() NodeKindIriOrBlank {
    return ConstructNodeKindIriOrBlankObject(&NodeKindIriOrBlankObject{}, nodeKindIriOrBlankType)
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

func (self *NodeKindIriOrBlankObject) Link(state *LinkState) error {
    if err := self.LinkClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *NodeKindIriOrBlankObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.LinkClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeNonShapeClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[NonShapeClass], error) {
    return DecodeRef[NonShapeClass](data, path, context, nonShapeClassType, check)
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
    return ConstructNonShapeClassObject(&NonShapeClassObject{}, self)
}

func ConstructNonShapeClassObject(o *NonShapeClassObject, typ SHACLType) *NonShapeClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    return o
}

type NonShapeClass interface {
    SHACLObject
}


func MakeNonShapeClass() NonShapeClass {
    return ConstructNonShapeClassObject(&NonShapeClassObject{}, nonShapeClassType)
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

func (self *NonShapeClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *NonShapeClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeParentClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[ParentClass], error) {
    return DecodeRef[ParentClass](data, path, context, parentClassType, check)
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
    return ConstructParentClassObject(&ParentClassObject{}, self)
}

func ConstructParentClassObject(o *ParentClassObject, typ SHACLType) *ParentClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    return o
}

type ParentClass interface {
    SHACLObject
}


func MakeParentClass() ParentClass {
    return ConstructParentClassObject(&ParentClassObject{}, parentClassType)
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

func (self *ParentClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *ParentClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeRequiredAbstract (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[RequiredAbstract], error) {
    return DecodeRef[RequiredAbstract](data, path, context, requiredAbstractType, check)
}

func (self RequiredAbstractObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(RequiredAbstract)
    _ = obj
    switch name {
    case "http://example.org/required-abstract/abstract-class-prop", "required-abstract/abstract-class-prop":
        val, err := DecodeAbstractClass(value, path, requiredAbstractRequiredAbstractAbstractClassPropContext, obj.RequiredAbstractAbstractClassProp())
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
    return ConstructRequiredAbstractObject(&RequiredAbstractObject{}, self)
}

func ConstructRequiredAbstractObject(o *RequiredAbstractObject, typ SHACLType) *RequiredAbstractObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    {
        validators := []Validator[Ref[AbstractClass]]{}
        decodeValidators := []Validator[any]{}
        o.requiredAbstractAbstractClassProp = NewRefProperty[AbstractClass]("requiredAbstractAbstractClassProp", validators, decodeValidators)
    }
    return o
}

type RequiredAbstract interface {
    SHACLObject
    RequiredAbstractAbstractClassProp() RefPropertyInterface[AbstractClass]
}


func MakeRequiredAbstract() RequiredAbstract {
    return ConstructRequiredAbstractObject(&RequiredAbstractObject{}, requiredAbstractType)
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

func (self *RequiredAbstractObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    if err := self.requiredAbstractAbstractClassProp.Link(state); err != nil {
        return err
    }
    return nil
}


func (self *RequiredAbstractObject) RequiredAbstractAbstractClassProp() RefPropertyInterface[AbstractClass] { return &self.requiredAbstractAbstractClassProp }

func (self *RequiredAbstractObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.requiredAbstractAbstractClassProp.IsSet() {
        val, err := EncodeRef[AbstractClass](self.requiredAbstractAbstractClassProp.Get(), path.PushPath("requiredAbstractAbstractClassProp"), requiredAbstractRequiredAbstractAbstractClassPropContext, state)
        if err != nil {
            return err
        }
        data["required-abstract/abstract-class-prop"] = val
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

func DecodeTestAnotherClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[TestAnotherClass], error) {
    return DecodeRef[TestAnotherClass](data, path, context, testAnotherClassType, check)
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
    return ConstructTestAnotherClassObject(&TestAnotherClassObject{}, self)
}

func ConstructTestAnotherClassObject(o *TestAnotherClassObject, typ SHACLType) *TestAnotherClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    return o
}

type TestAnotherClass interface {
    SHACLObject
}


func MakeTestAnotherClass() TestAnotherClass {
    return ConstructTestAnotherClassObject(&TestAnotherClassObject{}, testAnotherClassType)
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

func (self *TestAnotherClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *TestAnotherClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
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

func DecodeTestClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[TestClass], error) {
    return DecodeRef[TestClass](data, path, context, testClassType, check)
}

func (self TestClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestClass)
    _ = obj
    switch name {
    case "http://example.org/encode", "encode":
        val, err := DecodeString(value, path, testClassEncodeContext, obj.Encode())
        if err != nil {
            return false, err
        }
        err = obj.Encode().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/import", "import":
        val, err := DecodeString(value, path, testClassImportContext, obj.Import())
        if err != nil {
            return false, err
        }
        err = obj.Import().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/anyuri-prop", "test-class/anyuri-prop":
        val, err := DecodeString(value, path, testClassTestClassAnyuriPropContext, obj.TestClassAnyuriProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassAnyuriProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/boolean-prop", "test-class/boolean-prop":
        val, err := DecodeBoolean(value, path, testClassTestClassBooleanPropContext, obj.TestClassBooleanProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassBooleanProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-list-prop", "test-class/class-list-prop":
        val, err := DecodeList[Ref[TestClass]](value, path, testClassTestClassClassListPropContext, DecodeTestClass, obj.TestClassClassListProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassClassListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-prop", "test-class/class-prop":
        val, err := DecodeTestClass(value, path, testClassTestClassClassPropContext, obj.TestClassClassProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassClassProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/class-prop-no-class", "test-class/class-prop-no-class":
        val, err := DecodeTestClass(value, path, testClassTestClassClassPropNoClassContext, obj.TestClassClassPropNoClass())
        if err != nil {
            return false, err
        }
        err = obj.TestClassClassPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetime-list-prop", "test-class/datetime-list-prop":
        val, err := DecodeList[time.Time](value, path, testClassTestClassDatetimeListPropContext, DecodeDateTime, obj.TestClassDatetimeListProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassDatetimeListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetime-scalar-prop", "test-class/datetime-scalar-prop":
        val, err := DecodeDateTime(value, path, testClassTestClassDatetimeScalarPropContext, obj.TestClassDatetimeScalarProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassDatetimeScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/datetimestamp-scalar-prop", "test-class/datetimestamp-scalar-prop":
        val, err := DecodeDateTimeStamp(value, path, testClassTestClassDatetimestampScalarPropContext, obj.TestClassDatetimestampScalarProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassDatetimestampScalarProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-list-prop", "test-class/enum-list-prop":
        val, err := DecodeList[string](value, path, testClassTestClassEnumListPropContext, DecodeIRI, obj.TestClassEnumListProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassEnumListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-prop", "test-class/enum-prop":
        val, err := DecodeIRI(value, path, testClassTestClassEnumPropContext, obj.TestClassEnumProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassEnumProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/enum-prop-no-class", "test-class/enum-prop-no-class":
        val, err := DecodeIRI(value, path, testClassTestClassEnumPropNoClassContext, obj.TestClassEnumPropNoClass())
        if err != nil {
            return false, err
        }
        err = obj.TestClassEnumPropNoClass().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/float-prop", "test-class/float-prop":
        val, err := DecodeFloat(value, path, testClassTestClassFloatPropContext, obj.TestClassFloatProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassFloatProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/integer-prop", "test-class/integer-prop":
        val, err := DecodeInteger(value, path, testClassTestClassIntegerPropContext, obj.TestClassIntegerProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/named-property", "test-class/named-property":
        val, err := DecodeString(value, path, testClassNamedPropertyContext, obj.NamedProperty())
        if err != nil {
            return false, err
        }
        err = obj.NamedProperty().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/non-shape", "test-class/non-shape":
        val, err := DecodeNonShapeClass(value, path, testClassTestClassNonShapeContext, obj.TestClassNonShape())
        if err != nil {
            return false, err
        }
        err = obj.TestClassNonShape().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/nonnegative-integer-prop", "test-class/nonnegative-integer-prop":
        val, err := DecodeInteger(value, path, testClassTestClassNonnegativeIntegerPropContext, obj.TestClassNonnegativeIntegerProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassNonnegativeIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/positive-integer-prop", "test-class/positive-integer-prop":
        val, err := DecodeInteger(value, path, testClassTestClassPositiveIntegerPropContext, obj.TestClassPositiveIntegerProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassPositiveIntegerProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex", "test-class/regex":
        val, err := DecodeString(value, path, testClassTestClassRegexContext, obj.TestClassRegex())
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegex().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-datetime", "test-class/regex-datetime":
        val, err := DecodeDateTime(value, path, testClassTestClassRegexDatetimeContext, obj.TestClassRegexDatetime())
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegexDatetime().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-datetimestamp", "test-class/regex-datetimestamp":
        val, err := DecodeDateTimeStamp(value, path, testClassTestClassRegexDatetimestampContext, obj.TestClassRegexDatetimestamp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegexDatetimestamp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/regex-list", "test-class/regex-list":
        val, err := DecodeList[string](value, path, testClassTestClassRegexListContext, DecodeString, obj.TestClassRegexList())
        if err != nil {
            return false, err
        }
        err = obj.TestClassRegexList().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-list-no-datatype", "test-class/string-list-no-datatype":
        val, err := DecodeList[string](value, path, testClassTestClassStringListNoDatatypeContext, DecodeString, obj.TestClassStringListNoDatatype())
        if err != nil {
            return false, err
        }
        err = obj.TestClassStringListNoDatatype().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-list-prop", "test-class/string-list-prop":
        val, err := DecodeList[string](value, path, testClassTestClassStringListPropContext, DecodeString, obj.TestClassStringListProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassStringListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/string-scalar-prop", "test-class/string-scalar-prop":
        val, err := DecodeString(value, path, testClassTestClassStringScalarPropContext, obj.TestClassStringScalarProp())
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
    return ConstructTestClassObject(&TestClassObject{}, self)
}

func ConstructTestClassObject(o *TestClassObject, typ SHACLType) *TestClassObject {
    ConstructParentClassObject(&o.ParentClassObject, typ)
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.encode = NewProperty[string]("encode", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.import_ = NewProperty[string]("import_", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testClassAnyuriProp = NewProperty[string]("testClassAnyuriProp", validators, decodeValidators)
    }
    {
        validators := []Validator[bool]{}
        decodeValidators := []Validator[any]{}
        o.testClassBooleanProp = NewProperty[bool]("testClassBooleanProp", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[TestClass]]{}
        decodeValidators := []Validator[any]{}
        o.testClassClassListProp = NewRefListProperty[TestClass]("testClassClassListProp", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[TestClass]]{}
        decodeValidators := []Validator[any]{}
        o.testClassClassProp = NewRefProperty[TestClass]("testClassClassProp", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[TestClass]]{}
        decodeValidators := []Validator[any]{}
        o.testClassClassPropNoClass = NewRefProperty[TestClass]("testClassClassPropNoClass", validators, decodeValidators)
    }
    {
        validators := []Validator[time.Time]{}
        decodeValidators := []Validator[any]{}
        o.testClassDatetimeListProp = NewListProperty[time.Time]("testClassDatetimeListProp", validators, decodeValidators)
    }
    {
        validators := []Validator[time.Time]{}
        decodeValidators := []Validator[any]{}
        o.testClassDatetimeScalarProp = NewProperty[time.Time]("testClassDatetimeScalarProp", validators, decodeValidators)
    }
    {
        validators := []Validator[time.Time]{}
        decodeValidators := []Validator[any]{}
        o.testClassDatetimestampScalarProp = NewProperty[time.Time]("testClassDatetimestampScalarProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators,
            EnumValidator{[]string{
                "http://example.org/enumType/bar",
                "http://example.org/enumType/foo",
                "http://example.org/enumType/nolabel",
                "http://example.org/enumType/non-named-individual",
        }})
        o.testClassEnumListProp = NewListProperty[string]("testClassEnumListProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators,
            EnumValidator{[]string{
                "http://example.org/enumType/bar",
                "http://example.org/enumType/foo",
                "http://example.org/enumType/nolabel",
                "http://example.org/enumType/non-named-individual",
        }})
        o.testClassEnumProp = NewProperty[string]("testClassEnumProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators,
            EnumValidator{[]string{
                "http://example.org/enumType/bar",
                "http://example.org/enumType/foo",
                "http://example.org/enumType/nolabel",
                "http://example.org/enumType/non-named-individual",
        }})
        o.testClassEnumPropNoClass = NewProperty[string]("testClassEnumPropNoClass", validators, decodeValidators)
    }
    {
        validators := []Validator[float64]{}
        decodeValidators := []Validator[any]{}
        o.testClassFloatProp = NewProperty[float64]("testClassFloatProp", validators, decodeValidators)
    }
    {
        validators := []Validator[int]{}
        decodeValidators := []Validator[any]{}
        o.testClassIntegerProp = NewProperty[int]("testClassIntegerProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.namedProperty = NewProperty[string]("namedProperty", validators, decodeValidators)
    }
    {
        validators := []Validator[Ref[NonShapeClass]]{}
        decodeValidators := []Validator[any]{}
        o.testClassNonShape = NewRefProperty[NonShapeClass]("testClassNonShape", validators, decodeValidators)
    }
    {
        validators := []Validator[int]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators, IntegerMinValidator{0})
        o.testClassNonnegativeIntegerProp = NewProperty[int]("testClassNonnegativeIntegerProp", validators, decodeValidators)
    }
    {
        validators := []Validator[int]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators, IntegerMinValidator{1})
        o.testClassPositiveIntegerProp = NewProperty[int]("testClassPositiveIntegerProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators, RegexValidator[string]{`^foo\d`})
        decodeValidators = append(decodeValidators, RegexValidator[any]{`^foo\d`})
        o.testClassRegex = NewProperty[string]("testClassRegex", validators, decodeValidators)
    }
    {
        validators := []Validator[time.Time]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators, RegexValidator[time.Time]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+01:00$`})
        decodeValidators = append(decodeValidators, RegexValidator[any]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+01:00$`})
        o.testClassRegexDatetime = NewProperty[time.Time]("testClassRegexDatetime", validators, decodeValidators)
    }
    {
        validators := []Validator[time.Time]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators, RegexValidator[time.Time]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$`})
        decodeValidators = append(decodeValidators, RegexValidator[any]{`^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$`})
        o.testClassRegexDatetimestamp = NewProperty[time.Time]("testClassRegexDatetimestamp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        validators = append(validators, RegexValidator[string]{`^foo\d`})
        decodeValidators = append(decodeValidators, RegexValidator[any]{`^foo\d`})
        o.testClassRegexList = NewListProperty[string]("testClassRegexList", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testClassStringListNoDatatype = NewListProperty[string]("testClassStringListNoDatatype", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testClassStringListProp = NewListProperty[string]("testClassStringListProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testClassStringScalarProp = NewProperty[string]("testClassStringScalarProp", validators, decodeValidators)
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
    return ConstructTestClassObject(&TestClassObject{}, testClassType)
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

func (self *TestClassObject) Link(state *LinkState) error {
    if err := self.ParentClassObject.Link(state); err != nil {
        return err
    }
    if err := self.encode.Link(state); err != nil {
        return err
    }
    if err := self.import_.Link(state); err != nil {
        return err
    }
    if err := self.testClassAnyuriProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassBooleanProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassClassListProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassClassProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassClassPropNoClass.Link(state); err != nil {
        return err
    }
    if err := self.testClassDatetimeListProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassDatetimeScalarProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassDatetimestampScalarProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassEnumListProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassEnumProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassEnumPropNoClass.Link(state); err != nil {
        return err
    }
    if err := self.testClassFloatProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassIntegerProp.Link(state); err != nil {
        return err
    }
    if err := self.namedProperty.Link(state); err != nil {
        return err
    }
    if err := self.testClassNonShape.Link(state); err != nil {
        return err
    }
    if err := self.testClassNonnegativeIntegerProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassPositiveIntegerProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassRegex.Link(state); err != nil {
        return err
    }
    if err := self.testClassRegexDatetime.Link(state); err != nil {
        return err
    }
    if err := self.testClassRegexDatetimestamp.Link(state); err != nil {
        return err
    }
    if err := self.testClassRegexList.Link(state); err != nil {
        return err
    }
    if err := self.testClassStringListNoDatatype.Link(state); err != nil {
        return err
    }
    if err := self.testClassStringListProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassStringScalarProp.Link(state); err != nil {
        return err
    }
    return nil
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

func (self *TestClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.ParentClassObject.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.encode.IsSet() {
        val, err := EncodeString(self.encode.Get(), path.PushPath("encode"), testClassEncodeContext, state)
        if err != nil {
            return err
        }
        data["encode"] = val
    }
    if self.import_.IsSet() {
        val, err := EncodeString(self.import_.Get(), path.PushPath("import_"), testClassImportContext, state)
        if err != nil {
            return err
        }
        data["import"] = val
    }
    if self.testClassAnyuriProp.IsSet() {
        val, err := EncodeString(self.testClassAnyuriProp.Get(), path.PushPath("testClassAnyuriProp"), testClassTestClassAnyuriPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/anyuri-prop"] = val
    }
    if self.testClassBooleanProp.IsSet() {
        val, err := EncodeBoolean(self.testClassBooleanProp.Get(), path.PushPath("testClassBooleanProp"), testClassTestClassBooleanPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/boolean-prop"] = val
    }
    if self.testClassClassListProp.IsSet() {
        val, err := EncodeList[Ref[TestClass]](self.testClassClassListProp.Get(), path.PushPath("testClassClassListProp"), testClassTestClassClassListPropContext, state, EncodeRef[TestClass])
        if err != nil {
            return err
        }
        data["test-class/class-list-prop"] = val
    }
    if self.testClassClassProp.IsSet() {
        val, err := EncodeRef[TestClass](self.testClassClassProp.Get(), path.PushPath("testClassClassProp"), testClassTestClassClassPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/class-prop"] = val
    }
    if self.testClassClassPropNoClass.IsSet() {
        val, err := EncodeRef[TestClass](self.testClassClassPropNoClass.Get(), path.PushPath("testClassClassPropNoClass"), testClassTestClassClassPropNoClassContext, state)
        if err != nil {
            return err
        }
        data["test-class/class-prop-no-class"] = val
    }
    if self.testClassDatetimeListProp.IsSet() {
        val, err := EncodeList[time.Time](self.testClassDatetimeListProp.Get(), path.PushPath("testClassDatetimeListProp"), testClassTestClassDatetimeListPropContext, state, EncodeDateTime)
        if err != nil {
            return err
        }
        data["test-class/datetime-list-prop"] = val
    }
    if self.testClassDatetimeScalarProp.IsSet() {
        val, err := EncodeDateTime(self.testClassDatetimeScalarProp.Get(), path.PushPath("testClassDatetimeScalarProp"), testClassTestClassDatetimeScalarPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/datetime-scalar-prop"] = val
    }
    if self.testClassDatetimestampScalarProp.IsSet() {
        val, err := EncodeDateTime(self.testClassDatetimestampScalarProp.Get(), path.PushPath("testClassDatetimestampScalarProp"), testClassTestClassDatetimestampScalarPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/datetimestamp-scalar-prop"] = val
    }
    if self.testClassEnumListProp.IsSet() {
        val, err := EncodeList[string](self.testClassEnumListProp.Get(), path.PushPath("testClassEnumListProp"), testClassTestClassEnumListPropContext, state, EncodeIRI)
        if err != nil {
            return err
        }
        data["test-class/enum-list-prop"] = val
    }
    if self.testClassEnumProp.IsSet() {
        val, err := EncodeIRI(self.testClassEnumProp.Get(), path.PushPath("testClassEnumProp"), testClassTestClassEnumPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/enum-prop"] = val
    }
    if self.testClassEnumPropNoClass.IsSet() {
        val, err := EncodeIRI(self.testClassEnumPropNoClass.Get(), path.PushPath("testClassEnumPropNoClass"), testClassTestClassEnumPropNoClassContext, state)
        if err != nil {
            return err
        }
        data["test-class/enum-prop-no-class"] = val
    }
    if self.testClassFloatProp.IsSet() {
        val, err := EncodeFloat(self.testClassFloatProp.Get(), path.PushPath("testClassFloatProp"), testClassTestClassFloatPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/float-prop"] = val
    }
    if self.testClassIntegerProp.IsSet() {
        val, err := EncodeInteger(self.testClassIntegerProp.Get(), path.PushPath("testClassIntegerProp"), testClassTestClassIntegerPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/integer-prop"] = val
    }
    if self.namedProperty.IsSet() {
        val, err := EncodeString(self.namedProperty.Get(), path.PushPath("namedProperty"), testClassNamedPropertyContext, state)
        if err != nil {
            return err
        }
        data["test-class/named-property"] = val
    }
    if self.testClassNonShape.IsSet() {
        val, err := EncodeRef[NonShapeClass](self.testClassNonShape.Get(), path.PushPath("testClassNonShape"), testClassTestClassNonShapeContext, state)
        if err != nil {
            return err
        }
        data["test-class/non-shape"] = val
    }
    if self.testClassNonnegativeIntegerProp.IsSet() {
        val, err := EncodeInteger(self.testClassNonnegativeIntegerProp.Get(), path.PushPath("testClassNonnegativeIntegerProp"), testClassTestClassNonnegativeIntegerPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/nonnegative-integer-prop"] = val
    }
    if self.testClassPositiveIntegerProp.IsSet() {
        val, err := EncodeInteger(self.testClassPositiveIntegerProp.Get(), path.PushPath("testClassPositiveIntegerProp"), testClassTestClassPositiveIntegerPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/positive-integer-prop"] = val
    }
    if self.testClassRegex.IsSet() {
        val, err := EncodeString(self.testClassRegex.Get(), path.PushPath("testClassRegex"), testClassTestClassRegexContext, state)
        if err != nil {
            return err
        }
        data["test-class/regex"] = val
    }
    if self.testClassRegexDatetime.IsSet() {
        val, err := EncodeDateTime(self.testClassRegexDatetime.Get(), path.PushPath("testClassRegexDatetime"), testClassTestClassRegexDatetimeContext, state)
        if err != nil {
            return err
        }
        data["test-class/regex-datetime"] = val
    }
    if self.testClassRegexDatetimestamp.IsSet() {
        val, err := EncodeDateTime(self.testClassRegexDatetimestamp.Get(), path.PushPath("testClassRegexDatetimestamp"), testClassTestClassRegexDatetimestampContext, state)
        if err != nil {
            return err
        }
        data["test-class/regex-datetimestamp"] = val
    }
    if self.testClassRegexList.IsSet() {
        val, err := EncodeList[string](self.testClassRegexList.Get(), path.PushPath("testClassRegexList"), testClassTestClassRegexListContext, state, EncodeString)
        if err != nil {
            return err
        }
        data["test-class/regex-list"] = val
    }
    if self.testClassStringListNoDatatype.IsSet() {
        val, err := EncodeList[string](self.testClassStringListNoDatatype.Get(), path.PushPath("testClassStringListNoDatatype"), testClassTestClassStringListNoDatatypeContext, state, EncodeString)
        if err != nil {
            return err
        }
        data["test-class/string-list-no-datatype"] = val
    }
    if self.testClassStringListProp.IsSet() {
        val, err := EncodeList[string](self.testClassStringListProp.Get(), path.PushPath("testClassStringListProp"), testClassTestClassStringListPropContext, state, EncodeString)
        if err != nil {
            return err
        }
        data["test-class/string-list-prop"] = val
    }
    if self.testClassStringScalarProp.IsSet() {
        val, err := EncodeString(self.testClassStringScalarProp.Get(), path.PushPath("testClassStringScalarProp"), testClassTestClassStringScalarPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/string-scalar-prop"] = val
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

func DecodeTestClassRequired (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[TestClassRequired], error) {
    return DecodeRef[TestClassRequired](data, path, context, testClassRequiredType, check)
}

func (self TestClassRequiredObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestClassRequired)
    _ = obj
    switch name {
    case "http://example.org/test-class/required-string-list-prop", "test-class/required-string-list-prop":
        val, err := DecodeList[string](value, path, testClassRequiredTestClassRequiredStringListPropContext, DecodeString, obj.TestClassRequiredStringListProp())
        if err != nil {
            return false, err
        }
        err = obj.TestClassRequiredStringListProp().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/test-class/required-string-scalar-prop", "test-class/required-string-scalar-prop":
        val, err := DecodeString(value, path, testClassRequiredTestClassRequiredStringScalarPropContext, obj.TestClassRequiredStringScalarProp())
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
    return ConstructTestClassRequiredObject(&TestClassRequiredObject{}, self)
}

func ConstructTestClassRequiredObject(o *TestClassRequiredObject, typ SHACLType) *TestClassRequiredObject {
    ConstructTestClassObject(&o.TestClassObject, typ)
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testClassRequiredStringListProp = NewListProperty[string]("testClassRequiredStringListProp", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testClassRequiredStringScalarProp = NewProperty[string]("testClassRequiredStringScalarProp", validators, decodeValidators)
    }
    return o
}

type TestClassRequired interface {
    TestClass
    TestClassRequiredStringListProp() ListPropertyInterface[string]
    TestClassRequiredStringScalarProp() PropertyInterface[string]
}


func MakeTestClassRequired() TestClassRequired {
    return ConstructTestClassRequiredObject(&TestClassRequiredObject{}, testClassRequiredType)
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

func (self *TestClassRequiredObject) Link(state *LinkState) error {
    if err := self.TestClassObject.Link(state); err != nil {
        return err
    }
    if err := self.testClassRequiredStringListProp.Link(state); err != nil {
        return err
    }
    if err := self.testClassRequiredStringScalarProp.Link(state); err != nil {
        return err
    }
    return nil
}


func (self *TestClassRequiredObject) TestClassRequiredStringListProp() ListPropertyInterface[string] { return &self.testClassRequiredStringListProp }
func (self *TestClassRequiredObject) TestClassRequiredStringScalarProp() PropertyInterface[string] { return &self.testClassRequiredStringScalarProp }

func (self *TestClassRequiredObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.TestClassObject.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.testClassRequiredStringListProp.IsSet() {
        val, err := EncodeList[string](self.testClassRequiredStringListProp.Get(), path.PushPath("testClassRequiredStringListProp"), testClassRequiredTestClassRequiredStringListPropContext, state, EncodeString)
        if err != nil {
            return err
        }
        data["test-class/required-string-list-prop"] = val
    }
    if self.testClassRequiredStringScalarProp.IsSet() {
        val, err := EncodeString(self.testClassRequiredStringScalarProp.Get(), path.PushPath("testClassRequiredStringScalarProp"), testClassRequiredTestClassRequiredStringScalarPropContext, state)
        if err != nil {
            return err
        }
        data["test-class/required-string-scalar-prop"] = val
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

func DecodeTestDerivedClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[TestDerivedClass], error) {
    return DecodeRef[TestDerivedClass](data, path, context, testDerivedClassType, check)
}

func (self TestDerivedClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(TestDerivedClass)
    _ = obj
    switch name {
    case "http://example.org/test-derived-class/string-prop", "test-derived-class/string-prop":
        val, err := DecodeString(value, path, testDerivedClassTestDerivedClassStringPropContext, obj.TestDerivedClassStringProp())
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
    return ConstructTestDerivedClassObject(&TestDerivedClassObject{}, self)
}

func ConstructTestDerivedClassObject(o *TestDerivedClassObject, typ SHACLType) *TestDerivedClassObject {
    ConstructTestClassObject(&o.TestClassObject, typ)
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.testDerivedClassStringProp = NewProperty[string]("testDerivedClassStringProp", validators, decodeValidators)
    }
    return o
}

type TestDerivedClass interface {
    TestClass
    TestDerivedClassStringProp() PropertyInterface[string]
}


func MakeTestDerivedClass() TestDerivedClass {
    return ConstructTestDerivedClassObject(&TestDerivedClassObject{}, testDerivedClassType)
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

func (self *TestDerivedClassObject) Link(state *LinkState) error {
    if err := self.TestClassObject.Link(state); err != nil {
        return err
    }
    if err := self.testDerivedClassStringProp.Link(state); err != nil {
        return err
    }
    return nil
}


func (self *TestDerivedClassObject) TestDerivedClassStringProp() PropertyInterface[string] { return &self.testDerivedClassStringProp }

func (self *TestDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.TestClassObject.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.testDerivedClassStringProp.IsSet() {
        val, err := EncodeString(self.testDerivedClassStringProp.Get(), path.PushPath("testDerivedClassStringProp"), testDerivedClassTestDerivedClassStringPropContext, state)
        if err != nil {
            return err
        }
        data["test-derived-class/string-prop"] = val
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

func DecodeUsesExtensibleAbstractClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[UsesExtensibleAbstractClass], error) {
    return DecodeRef[UsesExtensibleAbstractClass](data, path, context, usesExtensibleAbstractClassType, check)
}

func (self UsesExtensibleAbstractClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(UsesExtensibleAbstractClass)
    _ = obj
    switch name {
    case "http://example.org/uses-extensible-abstract-class/prop", "uses-extensible-abstract-class/prop":
        val, err := DecodeExtensibleAbstractClass(value, path, usesExtensibleAbstractClassUsesExtensibleAbstractClassPropContext, obj.UsesExtensibleAbstractClassProp())
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
    return ConstructUsesExtensibleAbstractClassObject(&UsesExtensibleAbstractClassObject{}, self)
}

func ConstructUsesExtensibleAbstractClassObject(o *UsesExtensibleAbstractClassObject, typ SHACLType) *UsesExtensibleAbstractClassObject {
    ConstructSHACLObjectBase(&o.SHACLObjectBase, typ)
    {
        validators := []Validator[Ref[ExtensibleAbstractClass]]{}
        decodeValidators := []Validator[any]{}
        o.usesExtensibleAbstractClassProp = NewRefProperty[ExtensibleAbstractClass]("usesExtensibleAbstractClassProp", validators, decodeValidators)
    }
    return o
}

type UsesExtensibleAbstractClass interface {
    SHACLObject
    UsesExtensibleAbstractClassProp() RefPropertyInterface[ExtensibleAbstractClass]
}


func MakeUsesExtensibleAbstractClass() UsesExtensibleAbstractClass {
    return ConstructUsesExtensibleAbstractClassObject(&UsesExtensibleAbstractClassObject{}, usesExtensibleAbstractClassType)
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

func (self *UsesExtensibleAbstractClassObject) Link(state *LinkState) error {
    if err := self.SHACLObjectBase.Link(state); err != nil {
        return err
    }
    if err := self.usesExtensibleAbstractClassProp.Link(state); err != nil {
        return err
    }
    return nil
}


func (self *UsesExtensibleAbstractClassObject) UsesExtensibleAbstractClassProp() RefPropertyInterface[ExtensibleAbstractClass] { return &self.usesExtensibleAbstractClassProp }

func (self *UsesExtensibleAbstractClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.SHACLObjectBase.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.usesExtensibleAbstractClassProp.IsSet() {
        val, err := EncodeRef[ExtensibleAbstractClass](self.usesExtensibleAbstractClassProp.Get(), path.PushPath("usesExtensibleAbstractClassProp"), usesExtensibleAbstractClassUsesExtensibleAbstractClassPropContext, state)
        if err != nil {
            return err
        }
        data["uses-extensible-abstract-class/prop"] = val
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

func DecodeAaaDerivedClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[AaaDerivedClass], error) {
    return DecodeRef[AaaDerivedClass](data, path, context, aaaDerivedClassType, check)
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
    return ConstructAaaDerivedClassObject(&AaaDerivedClassObject{}, self)
}

func ConstructAaaDerivedClassObject(o *AaaDerivedClassObject, typ SHACLType) *AaaDerivedClassObject {
    ConstructParentClassObject(&o.ParentClassObject, typ)
    return o
}

type AaaDerivedClass interface {
    ParentClass
}


func MakeAaaDerivedClass() AaaDerivedClass {
    return ConstructAaaDerivedClassObject(&AaaDerivedClassObject{}, aaaDerivedClassType)
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

func (self *AaaDerivedClassObject) Link(state *LinkState) error {
    if err := self.ParentClassObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *AaaDerivedClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.ParentClassObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeDerivedNodeKindIri (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[DerivedNodeKindIri], error) {
    return DecodeRef[DerivedNodeKindIri](data, path, context, derivedNodeKindIriType, check)
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
    return ConstructDerivedNodeKindIriObject(&DerivedNodeKindIriObject{}, self)
}

func ConstructDerivedNodeKindIriObject(o *DerivedNodeKindIriObject, typ SHACLType) *DerivedNodeKindIriObject {
    ConstructNodeKindIriObject(&o.NodeKindIriObject, typ)
    return o
}

type DerivedNodeKindIri interface {
    NodeKindIri
}


func MakeDerivedNodeKindIri() DerivedNodeKindIri {
    return ConstructDerivedNodeKindIriObject(&DerivedNodeKindIriObject{}, derivedNodeKindIriType)
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

func (self *DerivedNodeKindIriObject) Link(state *LinkState) error {
    if err := self.NodeKindIriObject.Link(state); err != nil {
        return err
    }
    return nil
}



func (self *DerivedNodeKindIriObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.NodeKindIriObject.EncodeProperties(data, path, state); err != nil {
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

func DecodeExtensibleClass (data any, path Path, context map[string]string, check DecodeCheckType) (Ref[ExtensibleClass], error) {
    return DecodeRef[ExtensibleClass](data, path, context, extensibleClassType, check)
}

func (self ExtensibleClassObjectType) DecodeProperty(o SHACLObject, name string, value interface{}, path Path) (bool, error) {
    obj := o.(ExtensibleClass)
    _ = obj
    switch name {
    case "http://example.org/extensible-class/property", "extensible-class/property":
        val, err := DecodeString(value, path, extensibleClassExtensibleClassPropertyContext, obj.ExtensibleClassProperty())
        if err != nil {
            return false, err
        }
        err = obj.ExtensibleClassProperty().Set(val)
        if err != nil {
            return false, err
        }
        return true, nil
    case "http://example.org/extensible-class/required", "extensible-class/required":
        val, err := DecodeString(value, path, extensibleClassExtensibleClassRequiredContext, obj.ExtensibleClassRequired())
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
    return ConstructExtensibleClassObject(&ExtensibleClassObject{}, self)
}

func ConstructExtensibleClassObject(o *ExtensibleClassObject, typ SHACLType) *ExtensibleClassObject {
    ConstructLinkClassObject(&o.LinkClassObject, typ)
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.extensibleClassProperty = NewProperty[string]("extensibleClassProperty", validators, decodeValidators)
    }
    {
        validators := []Validator[string]{}
        decodeValidators := []Validator[any]{}
        o.extensibleClassRequired = NewProperty[string]("extensibleClassRequired", validators, decodeValidators)
    }
    return o
}

type ExtensibleClass interface {
    LinkClass
    ExtensibleClassProperty() PropertyInterface[string]
    ExtensibleClassRequired() PropertyInterface[string]
}


func MakeExtensibleClass() ExtensibleClass {
    return ConstructExtensibleClassObject(&ExtensibleClassObject{}, extensibleClassType)
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

func (self *ExtensibleClassObject) Link(state *LinkState) error {
    if err := self.LinkClassObject.Link(state); err != nil {
        return err
    }
    if err := self.extensibleClassProperty.Link(state); err != nil {
        return err
    }
    if err := self.extensibleClassRequired.Link(state); err != nil {
        return err
    }
    return nil
}


func (self *ExtensibleClassObject) ExtensibleClassProperty() PropertyInterface[string] { return &self.extensibleClassProperty }
func (self *ExtensibleClassObject) ExtensibleClassRequired() PropertyInterface[string] { return &self.extensibleClassRequired }

func (self *ExtensibleClassObject) EncodeProperties(data map[string]interface{}, path Path, state *EncodeState) error {
    if err := self.LinkClassObject.EncodeProperties(data, path, state); err != nil {
        return err
    }
    if self.extensibleClassProperty.IsSet() {
        val, err := EncodeString(self.extensibleClassProperty.Get(), path.PushPath("extensibleClassProperty"), extensibleClassExtensibleClassPropertyContext, state)
        if err != nil {
            return err
        }
        data["extensible-class/property"] = val
    }
    if self.extensibleClassRequired.IsSet() {
        val, err := EncodeString(self.extensibleClassRequired.Get(), path.PushPath("extensibleClassRequired"), extensibleClassExtensibleClassRequiredContext, state)
        if err != nil {
            return err
        }
        data["extensible-class/required"] = val
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
