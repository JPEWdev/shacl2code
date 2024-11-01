//
//
//

package model

type ErrorHandler interface {
    HandleError(error, Path)
}
