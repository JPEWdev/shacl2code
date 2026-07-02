#!/usr/bin/env node
// SPDX-FileContributor: Arthit Suriyawongkul
// SPDX-FileCopyrightText: 2026 Joshua Watt
// SPDX-FileType: SOURCE
// SPDX-License-Identifier: MIT
//
// Validate a JSON Schema file against its meta-schema using ajv v8.
// Usage: ajv-compile.js <schema.json> [draft-version]
// draft-version: 2020-12 or 2019-09 (default: inferred from "$schema")
const fs = require("fs");

const schemaFile = process.argv[2];
const draftArg = process.argv[3];

if (!schemaFile) {
    console.error("Usage: ajv-compile.js <schema.json> [draft-version]");
    process.exit(2);
}

const draftMap = {
    "2020-12": "ajv/dist/2020",
    "2019-09": "ajv/dist/2019",
};

const schemaUriMap = {
    "https://json-schema.org/draft/2020-12/schema": "2020-12",
    "http://json-schema.org/draft/2020-12/schema": "2020-12",
    "https://json-schema.org/draft/2019-09/schema": "2019-09",
    "http://json-schema.org/draft/2019-09/schema": "2019-09",
};

let schema;
try {
    schema = JSON.parse(fs.readFileSync(schemaFile, "utf8"));
} catch (e) {
    console.error(`Failed to read/parse "${schemaFile}": ${e.message}`);
    process.exit(2);
}

let draft = draftArg;
if (!draft) {
    draft = schemaUriMap[schema.$schema?.replace(/#$/, "")];
    if (!draft) {
        console.error(
            `Unable to infer draft version from "$schema": ${schema.$schema}. ` +
                "Pass the draft version explicitly as the second argument.",
        );
        process.exit(2);
    }
}

const ajvModule = draftMap[draft];
if (!ajvModule) {
    console.error(`Unsupported draft version: ${draft}. Supported: ${Object.keys(draftMap).join(", ")}`);
    process.exit(2);
}

let Ajv;
try {
    Ajv = require(ajvModule);
} catch (e) {
    console.error(
        `Failed to load "${ajvModule}": ${e.message}\n` +
            'Run "npm --prefix scripts install" to install dependencies.',
    );
    process.exit(2);
}

const ajv = new Ajv();
try {
    ajv.compile(schema);
    console.log("schema is valid");
} catch (e) {
    console.error("schema is invalid:", e.message);
    process.exit(1);
}
