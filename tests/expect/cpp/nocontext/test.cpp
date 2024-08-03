/**
 * @file
 *
 * Generated C++ bindings from a SHACL model
 *
 * This file was automatically generated by shacl2code. DO NOT MANUALLY MODIFY IT
 *
 * SPDX-License-Identifier: MIT
 */

#include <exception>
#include <list>
#include <map>
#include <memory>
#include <optional>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <variant>
#include <vector>

/* */
#include "test.hpp"
namespace test {
/* */

using std::string_literals::operator""s;

#ifndef DOXYGEN_SKIP
// clang-format off
// Auto-Generated Implementation

// http_example_org_abstract_class

const http_example_org_abstract_class::TypeClass http_example_org_abstract_class::Type(
    "http://example.org/abstract-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_abstract_class::http_example_org_abstract_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_abstract_class::~http_example_org_abstract_class() {}


// http_example_org_abstract_sh_class

const http_example_org_abstract_sh_class::TypeClass http_example_org_abstract_sh_class::Type(
    "http://example.org/abstract-sh-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_abstract_sh_class::http_example_org_abstract_sh_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_abstract_sh_class::~http_example_org_abstract_sh_class() {}


// http_example_org_abstract_spdx_class

const http_example_org_abstract_spdx_class::TypeClass http_example_org_abstract_spdx_class::Type(
    "http://example.org/abstract-spdx-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_abstract_spdx_class::http_example_org_abstract_spdx_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_abstract_spdx_class::~http_example_org_abstract_spdx_class() {}


// http_example_org_concrete_class

const http_example_org_concrete_class::TypeClass http_example_org_concrete_class::Type(
    "http://example.org/concrete-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_concrete_class::http_example_org_concrete_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_abstract_class(type, typeIRIs)
{}

http_example_org_concrete_class::~http_example_org_concrete_class() {}


// http_example_org_concrete_sh_class

const http_example_org_concrete_sh_class::TypeClass http_example_org_concrete_sh_class::Type(
    "http://example.org/concrete-sh-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_concrete_sh_class::http_example_org_concrete_sh_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_abstract_sh_class(type, typeIRIs)
{}

http_example_org_concrete_sh_class::~http_example_org_concrete_sh_class() {}


// http_example_org_concrete_spdx_class

const http_example_org_concrete_spdx_class::TypeClass http_example_org_concrete_spdx_class::Type(
    "http://example.org/concrete-spdx-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_concrete_spdx_class::http_example_org_concrete_spdx_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_abstract_spdx_class(type, typeIRIs)
{}

http_example_org_concrete_spdx_class::~http_example_org_concrete_spdx_class() {}


// http_example_org_enumType

const http_example_org_enumType::TypeClass http_example_org_enumType::Type(
    "http://example.org/enumType",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_enumType::http_example_org_enumType(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_enumType::~http_example_org_enumType() {}
const NamedIndividual http_example_org_enumType::foo(
    &http_example_org_enumType::Type,
    "http://example.org/enumType/foo",
    {}
);
const NamedIndividual http_example_org_enumType::bar(
    &http_example_org_enumType::Type,
    "http://example.org/enumType/bar",
    {}
);
const NamedIndividual http_example_org_enumType::nolabel(
    &http_example_org_enumType::Type,
    "http://example.org/enumType/nolabel",
    {}
);


// http_example_org_extensible_abstract_class

const http_example_org_extensible_abstract_class::TypeClass http_example_org_extensible_abstract_class::Type(
    "http://example.org/extensible-abstract-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    true
);

http_example_org_extensible_abstract_class::http_example_org_extensible_abstract_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLExtensibleObject<SHACLObject>(type, typeIRIs)
{}

http_example_org_extensible_abstract_class::~http_example_org_extensible_abstract_class() {}


// http_example_org_id_prop_class

const http_example_org_id_prop_class::TypeClass http_example_org_id_prop_class::Type(
    "http://example.org/id-prop-class",
    {},
    "testid",
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_id_prop_class::http_example_org_id_prop_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_id_prop_class::~http_example_org_id_prop_class() {}


// http_example_org_inherited_id_prop_class

const http_example_org_inherited_id_prop_class::TypeClass http_example_org_inherited_id_prop_class::Type(
    "http://example.org/inherited-id-prop-class",
    {},
    "testid",
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_inherited_id_prop_class::http_example_org_inherited_id_prop_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_id_prop_class(type, typeIRIs)
{}

http_example_org_inherited_id_prop_class::~http_example_org_inherited_id_prop_class() {}


// http_example_org_link_class

const http_example_org_link_class::TypeClass http_example_org_link_class::Type(
    "http://example.org/link-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_link_class::http_example_org_link_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs),
    _extensible(
        this,
        "http://example.org/link-class-extensible",
        {},
        false,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _link_list_prop(
        this,
        "http://example.org/link-class-link-list-prop",
        {},
        {},
        {},
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _link_prop(
        this,
        "http://example.org/link-class-link-prop",
        {},
        false,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _link_prop_no_class(
        this,
        "http://example.org/link-class-link-prop-no-class",
        {},
        false,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    )
{}

http_example_org_link_class::~http_example_org_link_class() {}


// http_example_org_link_derived_class

const http_example_org_link_derived_class::TypeClass http_example_org_link_derived_class::Type(
    "http://example.org/link-derived-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_link_derived_class::http_example_org_link_derived_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_link_class(type, typeIRIs)
{}

http_example_org_link_derived_class::~http_example_org_link_derived_class() {}


// http_example_org_node_kind_blank

const http_example_org_node_kind_blank::TypeClass http_example_org_node_kind_blank::Type(
    "http://example.org/node-kind-blank",
    {},
    {},
    NodeKind::BlankNode,
    false
);

http_example_org_node_kind_blank::http_example_org_node_kind_blank(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_link_class(type, typeIRIs)
{}

http_example_org_node_kind_blank::~http_example_org_node_kind_blank() {}


// http_example_org_node_kind_iri

const http_example_org_node_kind_iri::TypeClass http_example_org_node_kind_iri::Type(
    "http://example.org/node-kind-iri",
    {},
    {},
    NodeKind::IRI,
    false
);

http_example_org_node_kind_iri::http_example_org_node_kind_iri(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_link_class(type, typeIRIs)
{}

http_example_org_node_kind_iri::~http_example_org_node_kind_iri() {}


// http_example_org_node_kind_iri_or_blank

const http_example_org_node_kind_iri_or_blank::TypeClass http_example_org_node_kind_iri_or_blank::Type(
    "http://example.org/node-kind-iri-or-blank",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_node_kind_iri_or_blank::http_example_org_node_kind_iri_or_blank(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_link_class(type, typeIRIs)
{}

http_example_org_node_kind_iri_or_blank::~http_example_org_node_kind_iri_or_blank() {}


// http_example_org_non_shape_class

const http_example_org_non_shape_class::TypeClass http_example_org_non_shape_class::Type(
    "http://example.org/non-shape-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_non_shape_class::http_example_org_non_shape_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_non_shape_class::~http_example_org_non_shape_class() {}


// http_example_org_parent_class

const http_example_org_parent_class::TypeClass http_example_org_parent_class::Type(
    "http://example.org/parent-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_parent_class::http_example_org_parent_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_parent_class::~http_example_org_parent_class() {}


// http_example_org_required_abstract

const http_example_org_required_abstract::TypeClass http_example_org_required_abstract::Type(
    "http://example.org/required-abstract",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_required_abstract::http_example_org_required_abstract(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs),
    _abstract_class_prop(
        this,
        "http://example.org/required-abstract/abstract-class-prop",
        {},
        true,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    )
{}

http_example_org_required_abstract::~http_example_org_required_abstract() {}


// http_example_org_test_another_class

const http_example_org_test_another_class::TypeClass http_example_org_test_another_class::Type(
    "http://example.org/test-another-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_test_another_class::http_example_org_test_another_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs)
{}

http_example_org_test_another_class::~http_example_org_test_another_class() {}


// http_example_org_test_class

const http_example_org_test_class::TypeClass http_example_org_test_class::Type(
    "http://example.org/test-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_test_class::http_example_org_test_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_parent_class(type, typeIRIs),
    _encode(
        this,
        "http://example.org/encode",
        {},
        false,
        std::optional<std::regex>()
    ),
    _import(
        this,
        "http://example.org/import",
        {},
        false,
        std::optional<std::regex>()
    ),
    _anyuri_prop(
        this,
        "http://example.org/test-class/anyuri-prop",
        {},
        false,
        std::optional<std::regex>()
    ),
    _boolean_prop(
        this,
        "http://example.org/test-class/boolean-prop",
        {},
        false,
        std::optional<std::regex>()
    ),
    _class_list_prop(
        this,
        "http://example.org/test-class/class-list-prop",
        {},
        {},
        {},
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _class_prop(
        this,
        "http://example.org/test-class/class-prop",
        {},
        false,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _class_prop_no_class(
        this,
        "http://example.org/test-class/class-prop-no-class",
        {},
        false,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _datetime_list_prop(
        this,
        "http://example.org/test-class/datetime-list-prop",
        {},
        {},
        {},
        std::optional<std::regex>()
    ),
    _datetime_scalar_prop(
        this,
        "http://example.org/test-class/datetime-scalar-prop",
        {},
        false,
        std::optional<std::regex>()
    ),
    _datetimestamp_scalar_prop(
        this,
        "http://example.org/test-class/datetimestamp-scalar-prop",
        {},
        false,
        std::optional<std::regex>()
    ),
    _enum_list_prop(
        this,
        "http://example.org/test-class/enum-list-prop",
        {},
        {},
        {},
        std::optional<std::regex>(),
        std::unordered_set<std::string>({
            "http://example.org/enumType/bar",
            "http://example.org/enumType/foo",
            "http://example.org/enumType/nolabel",
            "http://example.org/enumType/non-named-individual"
        }),
        PropertyContext::Context({
        })
    ),
    _enum_prop(
        this,
        "http://example.org/test-class/enum-prop",
        {},
        false,
        std::optional<std::regex>(),
        std::unordered_set<std::string>({
            "http://example.org/enumType/bar",
            "http://example.org/enumType/foo",
            "http://example.org/enumType/nolabel",
            "http://example.org/enumType/non-named-individual"
        }),
        PropertyContext::Context({
        })
    ),
    _enum_prop_no_class(
        this,
        "http://example.org/test-class/enum-prop-no-class",
        {},
        false,
        std::optional<std::regex>(),
        std::unordered_set<std::string>({
            "http://example.org/enumType/bar",
            "http://example.org/enumType/foo",
            "http://example.org/enumType/nolabel",
            "http://example.org/enumType/non-named-individual"
        }),
        PropertyContext::Context({
        })
    ),
    _float_prop(
        this,
        "http://example.org/test-class/float-prop",
        {},
        false,
        std::optional<std::regex>()
    ),
    _integer_prop(
        this,
        "http://example.org/test-class/integer-prop",
        {},
        false,
        std::optional<std::regex>()
    ),
    _named_property(
        this,
        "http://example.org/test-class/named-property",
        {},
        false,
        std::optional<std::regex>()
    ),
    _non_shape(
        this,
        "http://example.org/test-class/non-shape",
        {},
        false,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    ),
    _nonnegative_integer_prop(
        this,
        "http://example.org/test-class/nonnegative-integer-prop",
        {},
        false,
        std::optional<std::regex>(),
        0
    ),
    _positive_integer_prop(
        this,
        "http://example.org/test-class/positive-integer-prop",
        {},
        false,
        std::optional<std::regex>(),
        1
    ),
    _regex(
        this,
        "http://example.org/test-class/regex",
        {},
        false,
        std::regex(R"REGEX(^foo\d)REGEX")
    ),
    _regex_datetime(
        this,
        "http://example.org/test-class/regex-datetime",
        {},
        false,
        std::regex(R"REGEX(^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d\+01:00$)REGEX")
    ),
    _regex_datetimestamp(
        this,
        "http://example.org/test-class/regex-datetimestamp",
        {},
        false,
        std::regex(R"REGEX(^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$)REGEX")
    ),
    _regex_list(
        this,
        "http://example.org/test-class/regex-list",
        {},
        {},
        {},
        std::regex(R"REGEX(^foo\d)REGEX")
    ),
    _string_list_no_datatype(
        this,
        "http://example.org/test-class/string-list-no-datatype",
        {},
        {},
        {},
        std::optional<std::regex>()
    ),
    _string_list_prop(
        this,
        "http://example.org/test-class/string-list-prop",
        {},
        {},
        {},
        std::optional<std::regex>()
    ),
    _string_scalar_prop(
        this,
        "http://example.org/test-class/string-scalar-prop",
        {},
        false,
        std::optional<std::regex>()
    )
{}

http_example_org_test_class::~http_example_org_test_class() {}
const NamedIndividual http_example_org_test_class::named(
    &http_example_org_test_class::Type,
    "http://example.org/test-class/named",
    {}
);


// http_example_org_test_class_required

const http_example_org_test_class_required::TypeClass http_example_org_test_class_required::Type(
    "http://example.org/test-class-required",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_test_class_required::http_example_org_test_class_required(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_test_class(type, typeIRIs),
    _required_string_list_prop(
        this,
        "http://example.org/test-class/required-string-list-prop",
        {},
        1,
        2,
        std::optional<std::regex>()
    ),
    _required_string_scalar_prop(
        this,
        "http://example.org/test-class/required-string-scalar-prop",
        {},
        true,
        std::optional<std::regex>()
    )
{}

http_example_org_test_class_required::~http_example_org_test_class_required() {}


// http_example_org_test_derived_class

const http_example_org_test_derived_class::TypeClass http_example_org_test_derived_class::Type(
    "http://example.org/test-derived-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_test_derived_class::http_example_org_test_derived_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_test_class(type, typeIRIs),
    _string_prop(
        this,
        "http://example.org/test-derived-class/string-prop",
        {},
        false,
        std::optional<std::regex>()
    )
{}

http_example_org_test_derived_class::~http_example_org_test_derived_class() {}


// http_example_org_uses_extensible_abstract_class

const http_example_org_uses_extensible_abstract_class::TypeClass http_example_org_uses_extensible_abstract_class::Type(
    "http://example.org/uses-extensible-abstract-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_uses_extensible_abstract_class::http_example_org_uses_extensible_abstract_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLObject(type, typeIRIs),
    _prop(
        this,
        "http://example.org/uses-extensible-abstract-class/prop",
        {},
        true,
        std::optional<std::regex>(),
        PropertyContext::Context({
        })
    )
{}

http_example_org_uses_extensible_abstract_class::~http_example_org_uses_extensible_abstract_class() {}


// http_example_org_aaa_derived_class

const http_example_org_aaa_derived_class::TypeClass http_example_org_aaa_derived_class::Type(
    "http://example.org/aaa-derived-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    false
);

http_example_org_aaa_derived_class::http_example_org_aaa_derived_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_parent_class(type, typeIRIs)
{}

http_example_org_aaa_derived_class::~http_example_org_aaa_derived_class() {}


// http_example_org_derived_node_kind_iri

const http_example_org_derived_node_kind_iri::TypeClass http_example_org_derived_node_kind_iri::Type(
    "http://example.org/derived-node-kind-iri",
    {},
    {},
    NodeKind::IRI,
    false
);

http_example_org_derived_node_kind_iri::http_example_org_derived_node_kind_iri(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    http_example_org_node_kind_iri(type, typeIRIs)
{}

http_example_org_derived_node_kind_iri::~http_example_org_derived_node_kind_iri() {}


// http_example_org_extensible_class

const http_example_org_extensible_class::TypeClass http_example_org_extensible_class::Type(
    "http://example.org/extensible-class",
    {},
    {},
    NodeKind::BlankNodeOrIRI,
    true
);

http_example_org_extensible_class::http_example_org_extensible_class(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs) :
    SHACLExtensibleObject<http_example_org_link_class>(type, typeIRIs),
    _property(
        this,
        "http://example.org/extensible-class/property",
        {},
        false,
        std::optional<std::regex>()
    ),
    _required(
        this,
        "http://example.org/extensible-class/required",
        {},
        true,
        std::optional<std::regex>()
    )
{}

http_example_org_extensible_class::~http_example_org_extensible_class() {}

#endif

// clang-format on

/* */
}
/* */
