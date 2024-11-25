/**
 * @file
 *
 * Generated C++ bindings from a SHACL model
 *
 * This file was automatically generated by shacl2code. DO NOT MANUALLY MODIFY IT
 *
 * SPDX-License-Identifier: MIT
 */

/* */
#ifndef _SHACL2CODE_TEST_LINK_HPP
#define _SHACL2CODE_TEST_LINK_HPP

/* */

#include <memory>
#include <set>
#include <string>
#include <unordered_set>

/* */
#ifndef DOXYGEN_SKIP
#include "api.hpp"
// These are so that we don't have to use Jinja templates below since that messes up the formatting
#define EXPORT SHACL2CODE_TEST_API
#define LOCAL  SHACL2CODE_TEST_LOCAL
#endif // DOXYGEN_SKIP

/* */
/* */
namespace test {
/* */

class SHACLObjectSet;
class SHACLObject;

/**
 * @brief Linking State
 *
 * Tracks the state while Linking objects in an object set
 */
class EXPORT LinkState {
   public:
    /// Constructor
    LinkState(SHACLObjectSet* o, std::set<std::string>* m);

    /// @copydoc ::test::SHACLObjectSet::findById()
    std::shared_ptr<SHACLObject> findObjById(
        std::string const& id,
        std::shared_ptr<SHACLObject> const& dflt = nullptr) const;

    /// A pointer to the SHACLObjectSet being linked
    SHACLObjectSet* const objectSet;

    /// A set of IRIs found during linking that had no corresponding object in
    /// the object set
    std::set<std::string>* const missing;

    /// Set of visited objects to prevent infinite recursion
    std::unordered_set<SHACLObject const*> visited;
};

/* */
#undef EXPORT
#undef LOCAL

/* */
/* */
}
/* */
/* */
#endif // _SHACL2CODE_TEST_LINK_HPP
/* */