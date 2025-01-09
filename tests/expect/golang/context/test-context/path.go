//
//
//

package model

import (
    "strconv"
    "strings"
)

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
