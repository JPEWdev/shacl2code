/**
 * @file
 *
 * Generated C++ bindings from a SHACL model
 *
 * This file was automatically generated by shacl2code. DO NOT MANUALLY MODIFY IT
 *
 * SPDX-License-Identifier: MIT
 */

// clang-format off
#ifndef _SHACL2CODE_TEST_HPP
#define _SHACL2CODE_TEST_HPP
// clang-format on

/* */
#include "api.hpp"
#include "datetime.hpp"
#include "decode.hpp"
#include "encode.hpp"
#include "errorhandler.hpp"
#include "exceptions.hpp"
#include "extensible.hpp"
#include "link.hpp"
#include "namedindividual.hpp"
#include "object.hpp"
#include "objectpath.hpp"
#include "objectset.hpp"
#include "prop.hpp"
#include "property.hpp"
#include "propertyvalue.hpp"
#include "ref.hpp"
#include "refproperty.hpp"
#include "type.hpp"
#include "util.hpp"
#include "walk.hpp"
/* */

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

/**
 * @defgroup test_concrete_classes test Concrete Classes
 *
 * These are the classes that can be directly instantiated in your code,
 * usually by invoking ::test::make_obj()
 */

// clang-format off

/**
 * @brief Abstract class constructor definition
 *
 * @note This is for internal use only
 */
#define SHACL2CODE_TEST_CONSTRUCTOR_ABSTRACT_true(name) name() = delete

/**
 * @brief Concrete class constructor definition
 *
 * @note This is for internal use only
 */
#define SHACL2CODE_TEST_CONSTRUCTOR_ABSTRACT_false(name) name() : name(&name::Type) {}

/**
 * @brief Define a TEST class
 *
 * This should be the first thing used in the class body to register it as a
 * class:
 *
 * @code
 *
 *  class MyClass : public MyParent {
 *      SHACL2CODE_TEST_CLASS(MyClass, MyParent, false)
 *      public:
 *          // Defined properties here
 *  };
 *
 * @endcode
 */
#define SHACL2CODE_TEST_CLASS(name, parent, abstract) \
    public: \
        using TypeClass = class SHACLType<name, parent, abstract>; \
        static const TypeClass Type; \
        SHACL2CODE_TEST_CONSTRUCTOR_ABSTRACT_##abstract(name); \
        virtual ~name(); \
        template<auto P, typename T> \
        auto& set(T const& value) { return SHACLObject::setHelper<P>(*this, value); } \
        template<auto P, typename T> \
        auto& add(T const& value) { return SHACLObject::addHelper<P>(*this, value); } \
    protected: \
        name(TypeBase const* type, SHACLObject::TypeIRIs const& typeIRIs = {}); \
        name(SHACLObject::TypeIRIs const& typeIRIs) : name(&name::Type, typeIRIs) {} ; \
    private: \
        friend TypeClass;

// Auto-Generated Classes
class http_example_org_abstract_class;
class http_example_org_abstract_sh_class;
class http_example_org_abstract_spdx_class;
class http_example_org_concrete_class;
class http_example_org_concrete_sh_class;
class http_example_org_concrete_spdx_class;
class http_example_org_enumType;
class http_example_org_extensible_abstract_class;
class http_example_org_id_prop_class;
class http_example_org_inherited_id_prop_class;
class http_example_org_link_class;
class http_example_org_link_derived_class;
class http_example_org_node_kind_blank;
class http_example_org_node_kind_iri;
class http_example_org_node_kind_iri_or_blank;
class http_example_org_non_shape_class;
class http_example_org_parent_class;
class http_example_org_required_abstract;
class http_example_org_test_another_class;
class http_example_org_test_class;
class http_example_org_test_class_required;
class http_example_org_test_derived_class;
class http_example_org_uses_extensible_abstract_class;
class http_example_org_aaa_derived_class;
class http_example_org_derived_node_kind_iri;
class http_example_org_extensible_class;
/**
 * @brief http_example_org_abstract_class
 *
 * IRI: http://example.org/abstract-class
 *
 * An Abstract class
 *
 *
 * This class is abstract
 */
class EXPORT http_example_org_abstract_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_abstract_class, SHACLObject, true)
   public:

    // Properties
};

/**
 * @brief http_example_org_abstract_sh_class
 *
 * IRI: http://example.org/abstract-sh-class
 *
 *
 *
 *
 * This class is abstract
 */
class EXPORT http_example_org_abstract_sh_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_abstract_sh_class, SHACLObject, true)
   public:

    // Properties
};

/**
 * @brief http_example_org_abstract_spdx_class
 *
 * IRI: http://example.org/abstract-spdx-class
 *
 * An Abstract class using the SPDX type
 *
 *
 * This class is abstract
 */
class EXPORT http_example_org_abstract_spdx_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_abstract_spdx_class, SHACLObject, true)
   public:

    // Properties
};

/**
 * @brief http_example_org_concrete_class
 *
 * IRI: http://example.org/concrete-class
 *
 * A concrete class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_concrete_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_concrete_class : public
    http_example_org_abstract_class {
   SHACL2CODE_TEST_CLASS(http_example_org_concrete_class, http_example_org_abstract_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_concrete_sh_class
 *
 * IRI: http://example.org/concrete-sh-class
 *
 * A concrete class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_concrete_sh_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_concrete_sh_class : public
    http_example_org_abstract_sh_class {
   SHACL2CODE_TEST_CLASS(http_example_org_concrete_sh_class, http_example_org_abstract_sh_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_concrete_spdx_class
 *
 * IRI: http://example.org/concrete-spdx-class
 *
 * A concrete class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_concrete_spdx_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_concrete_spdx_class : public
    http_example_org_abstract_spdx_class {
   SHACL2CODE_TEST_CLASS(http_example_org_concrete_spdx_class, http_example_org_abstract_spdx_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_enumType
 *
 * IRI: http://example.org/enumType
 *
 * An enumerated type
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_enumType>();
 *
 * @endcode
 */
class EXPORT http_example_org_enumType : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_enumType, SHACLObject, false)
   public:
    // Named Individuals
    /**
     * @brief bar
     *
     * IRI: http://example.org/enumType/bar
     *
     * The bar value of enumType
     */
    static const NamedIndividual bar;
    /**
     * @brief foo
     *
     * IRI: http://example.org/enumType/foo
     *
     * The foo value of enumType
     */
    static const NamedIndividual foo;
    /**
     * @brief nolabel
     *
     * IRI: http://example.org/enumType/nolabel
     *
     * This value has no label
     */
    static const NamedIndividual nolabel;

    // Properties
};

/**
 * @brief http_example_org_extensible_abstract_class
 *
 * IRI: http://example.org/extensible-abstract-class
 *
 * An extensible abstract class
 *
 *
 * This class is abstract
 */
class EXPORT http_example_org_extensible_abstract_class : public
    SHACLExtensibleObject<SHACLObject> {
   SHACL2CODE_TEST_CLASS(http_example_org_extensible_abstract_class, SHACLExtensibleObject<SHACLObject>, true)
   public:

    // Properties
};

/**
 * @brief http_example_org_id_prop_class
 *
 * IRI: http://example.org/id-prop-class
 *
 * A class with an ID alias
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_id_prop_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_id_prop_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_id_prop_class, SHACLObject, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_inherited_id_prop_class
 *
 * IRI: http://example.org/inherited-id-prop-class
 *
 * A class that inherits its idPropertyName from the parent
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_inherited_id_prop_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_inherited_id_prop_class : public
    http_example_org_id_prop_class {
   SHACL2CODE_TEST_CLASS(http_example_org_inherited_id_prop_class, http_example_org_id_prop_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_link_class
 *
 * IRI: http://example.org/link-class
 *
 * A class to test links
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_link_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_link_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_link_class, SHACLObject, false)
   public:

    // Properties
    /**
     * @brief extensible
     *
     * IRI: http://example.org/link-class-extensible
     *
     * A link to an extensible-class
     */
    Prop::Ref<http_example_org_extensible_class> _extensible;
    /**
     * @brief link_list_prop
     *
     * IRI: http://example.org/link-class-link-list-prop
     *
     * A link-class list property
     */
    Prop::RefList<http_example_org_link_class> _link_list_prop;
    /**
     * @brief link_prop
     *
     * IRI: http://example.org/link-class-link-prop
     *
     * A link-class property
     */
    Prop::Ref<http_example_org_link_class> _link_prop;
    /**
     * @brief link_prop_no_class
     *
     * IRI: http://example.org/link-class-link-prop-no-class
     *
     * A link-class property with no sh:class
     */
    Prop::Ref<http_example_org_link_class> _link_prop_no_class;
    /**
     * @brief tag
     *
     * IRI: http://example.org/link-class-tag
     *
     * Tag used to identify object for testing
     */
    Prop::String _tag;
};

/**
 * @brief http_example_org_link_derived_class
 *
 * IRI: http://example.org/link-derived-class
 *
 * A class derived from link-class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_link_derived_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_link_derived_class : public
    http_example_org_link_class {
   SHACL2CODE_TEST_CLASS(http_example_org_link_derived_class, http_example_org_link_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_node_kind_blank
 *
 * IRI: http://example.org/node-kind-blank
 *
 * A class that must be a blank node
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_node_kind_blank>();
 *
 * @endcode
 */
class EXPORT http_example_org_node_kind_blank : public
    http_example_org_link_class {
   SHACL2CODE_TEST_CLASS(http_example_org_node_kind_blank, http_example_org_link_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_node_kind_iri
 *
 * IRI: http://example.org/node-kind-iri
 *
 * A class that must be an IRI
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_node_kind_iri>();
 *
 * @endcode
 */
class EXPORT http_example_org_node_kind_iri : public
    http_example_org_link_class {
   SHACL2CODE_TEST_CLASS(http_example_org_node_kind_iri, http_example_org_link_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_node_kind_iri_or_blank
 *
 * IRI: http://example.org/node-kind-iri-or-blank
 *
 * A class that can be either a blank node or an IRI
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_node_kind_iri_or_blank>();
 *
 * @endcode
 */
class EXPORT http_example_org_node_kind_iri_or_blank : public
    http_example_org_link_class {
   SHACL2CODE_TEST_CLASS(http_example_org_node_kind_iri_or_blank, http_example_org_link_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_non_shape_class
 *
 * IRI: http://example.org/non-shape-class
 *
 * A class that is not a nodeshape
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_non_shape_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_non_shape_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_non_shape_class, SHACLObject, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_parent_class
 *
 * IRI: http://example.org/parent-class
 *
 * The parent class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_parent_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_parent_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_parent_class, SHACLObject, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_required_abstract
 *
 * IRI: http://example.org/required-abstract
 *
 * A class with a mandatory abstract class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_required_abstract>();
 *
 * @endcode
 */
class EXPORT http_example_org_required_abstract : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_required_abstract, SHACLObject, false)
   public:

    // Properties
    /**
     * @brief abstract_class_prop
     *
     * IRI: http://example.org/required-abstract/abstract-class-prop
     *
     * A required abstract class property
     */
    Prop::Ref<http_example_org_abstract_class> _abstract_class_prop;
};

/**
 * @brief http_example_org_test_another_class
 *
 * IRI: http://example.org/test-another-class
 *
 * Another class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_test_another_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_test_another_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_test_another_class, SHACLObject, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_test_class
 *
 * IRI: http://example.org/test-class
 *
 * The test class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_test_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_test_class : public
    http_example_org_parent_class {
   SHACL2CODE_TEST_CLASS(http_example_org_test_class, http_example_org_parent_class, false)
   public:
    // Named Individuals
    /**
     * @brief named
     *
     * IRI: http://example.org/test-class/named
     *
     *
     */
    static const NamedIndividual named;

    // Properties
    /**
     * @brief encode
     *
     * IRI: http://example.org/encode
     *
     * A property that conflicts with an existing SHACLObject property
     */
    Prop::String _encode;
    /**
     * @brief import
     *
     * IRI: http://example.org/import
     *
     * A property that is a keyword
     */
    Prop::String _import;
    /**
     * @brief anyuri_prop
     *
     * IRI: http://example.org/test-class/anyuri-prop
     *
     * a URI
     */
    Prop::AnyURI _anyuri_prop;
    /**
     * @brief boolean_prop
     *
     * IRI: http://example.org/test-class/boolean-prop
     *
     * a boolean property
     */
    Prop::Boolean _boolean_prop;
    /**
     * @brief class_list_prop
     *
     * IRI: http://example.org/test-class/class-list-prop
     *
     * A test-class list property
     */
    Prop::RefList<http_example_org_test_class> _class_list_prop;
    /**
     * @brief class_prop
     *
     * IRI: http://example.org/test-class/class-prop
     *
     * A test-class property
     */
    Prop::Ref<http_example_org_test_class> _class_prop;
    /**
     * @brief class_prop_no_class
     *
     * IRI: http://example.org/test-class/class-prop-no-class
     *
     * A test-class property with no sh:class
     */
    Prop::Ref<http_example_org_test_class> _class_prop_no_class;
    /**
     * @brief datetime_list_prop
     *
     * IRI: http://example.org/test-class/datetime-list-prop
     *
     * A datetime list property
     */
    Prop::DateTimeList _datetime_list_prop;
    /**
     * @brief datetime_scalar_prop
     *
     * IRI: http://example.org/test-class/datetime-scalar-prop
     *
     * A scalar datetime property
     */
    Prop::DateTime _datetime_scalar_prop;
    /**
     * @brief datetimestamp_scalar_prop
     *
     * IRI: http://example.org/test-class/datetimestamp-scalar-prop
     *
     * A scalar dateTimeStamp property
     */
    Prop::DateTimeStamp _datetimestamp_scalar_prop;
    /**
     * @brief enum_list_prop
     *
     * IRI: http://example.org/test-class/enum-list-prop
     *
     * A enum list property
     */
    Prop::EnumList _enum_list_prop;
    /**
     * @brief enum_prop
     *
     * IRI: http://example.org/test-class/enum-prop
     *
     * A enum property
     */
    Prop::Enum _enum_prop;
    /**
     * @brief enum_prop_no_class
     *
     * IRI: http://example.org/test-class/enum-prop-no-class
     *
     * A enum property with no sh:class
     */
    Prop::Enum _enum_prop_no_class;
    /**
     * @brief float_prop
     *
     * IRI: http://example.org/test-class/float-prop
     *
     * a float property
     */
    Prop::Double _float_prop;
    /**
     * @brief integer_prop
     *
     * IRI: http://example.org/test-class/integer-prop
     *
     * a non-negative integer
     */
    Prop::Integer _integer_prop;
    /**
     * @brief named_property
     *
     * IRI: http://example.org/test-class/named-property
     *
     * A named property
     */
    Prop::String _named_property;
    /**
     * @brief non_shape
     *
     * IRI: http://example.org/test-class/non-shape
     *
     * A class with no shape
     */
    Prop::Ref<http_example_org_non_shape_class> _non_shape;
    /**
     * @brief nonnegative_integer_prop
     *
     * IRI: http://example.org/test-class/nonnegative-integer-prop
     *
     * a non-negative integer
     */
    Prop::Integer _nonnegative_integer_prop;
    /**
     * @brief positive_integer_prop
     *
     * IRI: http://example.org/test-class/positive-integer-prop
     *
     * A positive integer
     */
    Prop::Integer _positive_integer_prop;
    /**
     * @brief regex
     *
     * IRI: http://example.org/test-class/regex
     *
     * A regex validated string
     */
    Prop::String _regex;
    /**
     * @brief regex_datetime
     *
     * IRI: http://example.org/test-class/regex-datetime
     *
     * A regex dateTime
     */
    Prop::DateTime _regex_datetime;
    /**
     * @brief regex_datetimestamp
     *
     * IRI: http://example.org/test-class/regex-datetimestamp
     *
     * A regex dateTimeStamp
     */
    Prop::DateTimeStamp _regex_datetimestamp;
    /**
     * @brief regex_list
     *
     * IRI: http://example.org/test-class/regex-list
     *
     * A regex validated string list
     */
    Prop::StringList _regex_list;
    /**
     * @brief string_list_no_datatype
     *
     * IRI: http://example.org/test-class/string-list-no-datatype
     *
     * A string list property with no sh:datatype
     */
    Prop::StringList _string_list_no_datatype;
    /**
     * @brief string_list_prop
     *
     * IRI: http://example.org/test-class/string-list-prop
     *
     * A string list property
     */
    Prop::StringList _string_list_prop;
    /**
     * @brief string_scalar_prop
     *
     * IRI: http://example.org/test-class/string-scalar-prop
     *
     * A scalar string propery
     */
    Prop::String _string_scalar_prop;
};

/**
 * @brief http_example_org_test_class_required
 *
 * IRI: http://example.org/test-class-required
 *
 *
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_test_class_required>();
 *
 * @endcode
 */
class EXPORT http_example_org_test_class_required : public
    http_example_org_test_class {
   SHACL2CODE_TEST_CLASS(http_example_org_test_class_required, http_example_org_test_class, false)
   public:

    // Properties
    /**
     * @brief required_string_list_prop
     *
     * IRI: http://example.org/test-class/required-string-list-prop
     *
     * A required string list property
     */
    Prop::StringList _required_string_list_prop;
    /**
     * @brief required_string_scalar_prop
     *
     * IRI: http://example.org/test-class/required-string-scalar-prop
     *
     * A required scalar string property
     */
    Prop::String _required_string_scalar_prop;
};

/**
 * @brief http_example_org_test_derived_class
 *
 * IRI: http://example.org/test-derived-class
 *
 * A class derived from test-class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_test_derived_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_test_derived_class : public
    http_example_org_test_class {
   SHACL2CODE_TEST_CLASS(http_example_org_test_derived_class, http_example_org_test_class, false)
   public:

    // Properties
    /**
     * @brief string_prop
     *
     * IRI: http://example.org/test-derived-class/string-prop
     *
     * A string property in a derived class
     */
    Prop::String _string_prop;
};

/**
 * @brief http_example_org_uses_extensible_abstract_class
 *
 * IRI: http://example.org/uses-extensible-abstract-class
 *
 * A class that uses an abstract extensible class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_uses_extensible_abstract_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_uses_extensible_abstract_class : public
    SHACLObject {
   SHACL2CODE_TEST_CLASS(http_example_org_uses_extensible_abstract_class, SHACLObject, false)
   public:

    // Properties
    /**
     * @brief prop
     *
     * IRI: http://example.org/uses-extensible-abstract-class/prop
     *
     * A property that references and abstract extensible class
     */
    Prop::Ref<http_example_org_extensible_abstract_class> _prop;
};

/**
 * @brief http_example_org_aaa_derived_class
 *
 * IRI: http://example.org/aaa-derived-class
 *
 * Derived class that sorts before the parent to test ordering
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_aaa_derived_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_aaa_derived_class : public
    http_example_org_parent_class {
   SHACL2CODE_TEST_CLASS(http_example_org_aaa_derived_class, http_example_org_parent_class, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_derived_node_kind_iri
 *
 * IRI: http://example.org/derived-node-kind-iri
 *
 * A class that derives its nodeKind from parent
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_derived_node_kind_iri>();
 *
 * @endcode
 */
class EXPORT http_example_org_derived_node_kind_iri : public
    http_example_org_node_kind_iri {
   SHACL2CODE_TEST_CLASS(http_example_org_derived_node_kind_iri, http_example_org_node_kind_iri, false)
   public:

    // Properties
};

/**
 * @brief http_example_org_extensible_class
 *
 * IRI: http://example.org/extensible-class
 *
 * An extensible class
 *
 *
 * @ingroup test_concrete_classes
 *
 * Example:
 * @code
 *  auto o = make_obj<http_example_org_extensible_class>();
 *
 * @endcode
 */
class EXPORT http_example_org_extensible_class : public
    SHACLExtensibleObject<http_example_org_link_class> {
   SHACL2CODE_TEST_CLASS(http_example_org_extensible_class, SHACLExtensibleObject<http_example_org_link_class>, false)
   public:

    // Properties
    /**
     * @brief property
     *
     * IRI: http://example.org/extensible-class/property
     *
     * An extensible property
     */
    Prop::String _property;
    /**
     * @brief required
     *
     * IRI: http://example.org/extensible-class/required
     *
     * A required extensible property
     */
    Prop::String _required;
};


// clang-format on

/* */
#undef EXPORT
#undef LOCAL

/* */
/* */
}
/* */

#endif  // _SHACL2CODE_TEST_HPP
