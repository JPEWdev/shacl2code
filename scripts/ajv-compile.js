#!/usr/bin/env node
// Validate a JSON Schema file against a JSON Schema meta-schema using ajv v8
// Usage: ajv-compile.js <schema.json> [draft-version]
// draft-version: 2020-12 (default), 2019-09
const fs = require("fs");
const { execSync } = require("child_process");
const path = require("path");

const schemaFile = process.argv[2];
const draft = process.argv[3] || "2020-12";

if (!schemaFile) {
    console.error("Usage: ajv-compile.js <schema.json> [draft-version]");
    process.exit(2);
}

const draftMap = {
    "2020-12": "ajv/dist/2020",
    "2019-09": "ajv/dist/2019",
};

const ajvModule = draftMap[draft];
if (!ajvModule) {
    console.error(`Unsupported draft version: ${draft}. Supported: ${Object.keys(draftMap).join(", ")}`);
    process.exit(2);
}

function requireAjv(moduleName) {
    try {
        return require(moduleName);
    } catch (e) {
        const globalRoot = execSync("npm root -g").toString().trim();
        return require(path.join(globalRoot, ...moduleName.split("/")));
    }
}

const Ajv = requireAjv(ajvModule);
const ajv = new Ajv();
const schema = JSON.parse(fs.readFileSync(schemaFile, "utf8"));
try {
    ajv.compile(schema);
    console.log("schema is valid");
} catch (e) {
    console.error("schema is invalid:", e.message);
    process.exit(1);
}
