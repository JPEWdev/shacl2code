//
//
//

package model

type RefListProperty[T SHACLObject] struct {
    ListProperty[Ref[T]]
}

func NewRefListProperty[T SHACLObject](name string, validators []Validator[Ref[T]], decodeValidators []Validator[any]) RefListProperty[T] {
    return RefListProperty[T]{
        ListProperty: ListProperty[Ref[T]]{
            value: []Ref[T]{},
            name: name,
            validators: validators,
            decodeValidators: decodeValidators,
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

func (self *RefListProperty[T]) Link(state *LinkState) error {
    for _, r := range self.value {
        if err := r.link(state); err != nil {
            return err
        }
    }
    return nil
}
