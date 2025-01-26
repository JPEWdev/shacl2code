/**
 * @file
 *
 * This file was automatically generated by shacl2code. DO NOT MANUALLY MODIFY IT
 *
 * SPDX-License-Identifier: 0BSD
 */

// clang-format off
#ifndef _SHACL2CODE_TEST_CONTEXT_JSONLD_HPP
#define _SHACL2CODE_TEST_CONTEXT_JSONLD_HPP
// clang-format on

#include <functional>
#include <istream>
#include <optional>
#include <ostream>
#include <string>

/* */
#include "test-context.hpp"
namespace test_context {
/* */

// clang-format off
#ifndef DOXYGEN_SKIP
#define EXPORT SHACL2CODE_TEST_CONTEXT_API
#define LOCAL SHACL2CODE_TEST_CONTEXT_LOCAL
#endif
// clang-format on

// Encode
/**
 * @brief JSONLD Encoder State
 *
 * The encoder state when encoding an JSONLD object
 */
class EXPORT JSONLDEncoderState : public EncoderState {
   public:
    /// Constructor
    JSONLDEncoderState(std::ostream& output);

    /// Destructor
    virtual ~JSONLDEncoderState();

    /**
     * @brief Write a comma
     *
     * Writes a comma to the output, if one is needed
     */
    void writeComma();

    /**
     * @brief Needs comma
     *
     * Marks that a comma may be needed before another item is written
     */
    void needsComma();

    /**
     * @brief Get Output
     *
     * @returns the output stream where the JSON should be written
     */
    std::ostream& output() const { return mOutput; }

   private:
    std::ostream& mOutput;
    bool mNeedsComma = false;
};

/**
 * @brief JSON LD Value Encoder
 *
 * Encodes a value using JSON LD
 */
class EXPORT JSONLDValueEncoder : public ValueEncoder {
   public:
    /// Constructor
    JSONLDValueEncoder(JSONLDEncoderState& state);

    /// Destructor
    virtual ~JSONLDValueEncoder();

    /// @copydoc ::test_context::ValueEncoder::writeString()
    void writeString(std::string const& value) override;

    /// @copydoc ::test_context::ValueEncoder::writeDateTime()
    void writeDateTime(DateTime const& value) override;

    /// @copydoc ::test_context::ValueEncoder::writeInteger()
    void writeInteger(int value) override;

    /// @copydoc ::test_context::ValueEncoder::writeIRI()
    void writeIRI(std::string const& value,
                  std::optional<std::string> const& compact = {}) override;

    /// @copydoc ::test_context::ValueEncoder::writeEnum()
    void writeEnum(std::string const& value,
                   std::optional<std::string> const& compact = {}) override;

    /// @copydoc ::test_context::ValueEncoder::writeBool()
    void writeBool(bool value) override;

    /// @copydoc ::test_context::ValueEncoder::writeFloat()
    void writeFloat(double value) override;

    /// @copydoc ::test_context::ValueEncoder::writeObject()
    void writeObject(SHACLObject const& o, std::string const& id, bool needs_id,
                     std::function<void(ObjectEncoder&)> const& f) override;

    /// @copydoc ::test_context::ValueEncoder::writeList()
    void writeList(std::function<void(ListEncoder&)> const& f) override;

   private:
    JSONLDEncoderState& mState;
};

/**
 * @brief JSON LD Object Encoder
 *
 * Encodes an object using JSON LD
 */
class EXPORT JSONLDObjectEncoder : public ObjectEncoder {
   public:
    /// Constructor
    JSONLDObjectEncoder(JSONLDEncoderState& state);

    /// Destructor
    virtual ~JSONLDObjectEncoder();

    /// @copydoc ::test_context::ObjectEncoder::writeProperty()
    void writeProperty(std::string const& iri,
                       std::optional<std::string> const& compact,
                       std::function<void(ValueEncoder&)> const& f) override;

   private:
    JSONLDEncoderState& mState;
};

/**
 * @brief JSON LD List Encoder
 *
 * Encoder a list using JSON LD
 */
class EXPORT JSONLDListEncoder : public ListEncoder {
   public:
    /// Constructor
    JSONLDListEncoder(JSONLDEncoderState& state);

    /// Destructor
    virtual ~JSONLDListEncoder();

    /// @copydoc ::test_context::ListEncoder::writeItem()
    void writeItem(std::function<void(ValueEncoder&)> const& f) override;

   private:
    JSONLDEncoderState& mState;
};

/**
 * @brief JSON LD Inline Serialize
 *
 * Writes a SHACLObjectSet to an output stream as JSON LD. This serialize is
 * "inline" in that it streams out the JSON as it serializes instead of
 * building up an internal JSON model. This method uses less memory, but the
 * output is all in one long line with little extraneous white space
 */
class EXPORT JSONLDInlineSerializer {
   public:
    /// Constructor
    JSONLDInlineSerializer();

    /// Destructor
    virtual ~JSONLDInlineSerializer();

    /**
     * @brief Write JSON LD
     *
     * Serializes the SHACLObjectSet as JSON LD
     *
     * @param output        The output stream where the objects will be written
     * @param objectSet     The objects to serialize
     * @param errorHandler  The ErrorHandler to use to report errors
     */
    void write(std::ostream& output, SHACLObjectSet& objectSet,
               ErrorHandler& errorHandler = DefaultErrorHandler::handler);
};

// Decode

struct JSONData;

/**
 * @brief JSON LD Value Decoder
 *
 * Decodes a value from JSON LD data
 */
class EXPORT JSONLDValueDecoder : public ValueDecoder {
   public:
    /// Constructor
    JSONLDValueDecoder(DecoderState& state, JSONData const& data);

    /// Destructor
    virtual ~JSONLDValueDecoder();

    /// @copydoc ::test_context::ValueDecoder::getType()
    ValueDecoder::Type getType() const override;

    /// @copydoc ::test_context::ValueDecoder::readString()
    std::optional<std::string> readString() override;

    /// @copydoc ::test_context::ValueDecoder::readDateTime()
    std::optional<DateTime> readDateTime() override;

    /// @copydoc ::test_context::ValueDecoder::readDateTimeStamp()
    std::optional<DateTime> readDateTimeStamp() override;

    /// @copydoc ::test_context::ValueDecoder::readInteger()
    std::optional<int> readInteger() override;

    /// @copydoc ::test_context::ValueDecoder::readIRI()
    std::optional<std::string> readIRI() override;

    /// @copydoc ::test_context::ValueDecoder::readEnum()
    std::optional<std::string> readEnum() override;

    /// @copydoc ::test_context::ValueDecoder::readBool()
    std::optional<bool> readBool() override;

    /// @copydoc ::test_context::ValueDecoder::readFloat()
    std::optional<double> readFloat() override;

    /// @copydoc ::test_context::ValueDecoder::readObject()
    bool readObject(std::function<void(ObjectDecoder&)> const& f) override;

    /// @copydoc ::test_context::ValueDecoder::readList()
    bool readList(std::function<void(ListDecoder&)> const& f) override;

   private:
    JSONData const& mData;
};

/**
 * @brief JSON LD Object Decoder
 *
 * Decodes an Object from JSON LD data
 */
class EXPORT JSONLDObjectDecoder : public ObjectDecoder {
   public:
    /// Constructor
    JSONLDObjectDecoder(DecoderState& state, JSONData const& data,
                        std::unordered_set<std::string> const& ignoreProperties = {});

    /// Destructor
    virtual ~JSONLDObjectDecoder();

    /// @copydoc ::test_context::ObjectDecoder::readType()
    std::optional<std::string> readType() override;

    /// @copydoc ::test_context::ObjectDecoder::readProperties()
    void readProperties(std::function<void(std::string const&,
                                           ValueDecoder&)> const& f) override;

   private:
    std::optional<std::string> readStringProp(std::string const& s);

    JSONData const& mData;
    std::unordered_set<std::string> mIgnoreProperties;
};

/**
 * @brief JSON LD List Decoder
 *
 * Decodes a list from JSON LD data
 */
class EXPORT JSONLDListDecoder : public ListDecoder {
   public:
    /// Constructor
    JSONLDListDecoder(DecoderState& state, JSONData const& data);

    /// Destructor
    virtual ~JSONLDListDecoder();

    /// @copydoc ::test_context::ListDecoder::readItems()
    void readItems(std::function<void(ValueDecoder&)> const& f) override;

   private:
    JSONData const& mData;
};

/**
 * @brief JSON LD Deserializer
 *
 * Deserializes a JSON LD document and places the resulting object in a
 * SHACLObjectSet
 */
class EXPORT JSONLDDeserializer {
   public:
    /// Constructor
    JSONLDDeserializer();

    /// Destructor
    virtual ~JSONLDDeserializer();

    /**
     * @brief Read JSON LD document
     *
     * Reads the input stream as JSON LD data and places deserialzied objects
     * in the SHACLObjectSet
     *
     * @param input         The input stream to read from
     * @param objectSet     The SHACLObjectSet where the objects will be placed
     * @param errorHandler  The ErrorHandler to use to report errors
     */
    void read(std::istream& input, SHACLObjectSet& objectSet,
              ErrorHandler& errorHandler = DefaultErrorHandler::handler);
};

#undef EXPORT
#undef LOCAL

/* */
}
/* */

#endif  // _SHACL2CODE_TEST_CONTEXT_JSONLD_HPP
