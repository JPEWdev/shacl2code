package runtime

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"github.com/pmezard/go-difflib/difflib"
)

/*
		SPDX compatible definitions for this test can be generated using something like:

	 .venv/bin/python -m shacl2code generate -i https://spdx.org/rdf/3.0.0/spdx-model.ttl -i https://spdx.org/rdf/3.0.0/spdx-json-serialize-annotations.ttl -x https://spdx.org/rdf/3.0.0/spdx-context.jsonld golang --package runtime --output src/shacl2code/lang/go_runtime/generated_code.go --remap-props element=elements,externalIdentifier=externalIdentifiers --include-runtime false
*/
func Test_spdxExportImportExport(t *testing.T) {
	doc := SpdxDocument{
		SpdxId:       "old-id",
		DataLicense:  nil,
		Imports:      nil,
		NamespaceMap: nil,
	}

	doc.SetSpdxId("new-id")

	agent := &SoftwareAgent{
		Name:    "some-agent",
		Summary: "summary",
	}
	c := &CreationInfo{
		Comment: "some-comment",
		Created: "",
		CreatedBy: []IAgent{
			agent,
		},
		CreatedUsing: []ITool{
			&Tool{
				ExternalIdentifiers: []IExternalIdentifier{
					&ExternalIdentifier{
						ExternalIdentifierType: ExternalIdentifierType_Cpe23,
						Identifier:             "cpe23:a:myvendor:my-product:*:*:*:*:*:*:*",
					},
				},
				Name: "not-tools-golang",
			},
		},
		SpecVersion: "",
	}
	agent.SetCreationInfo(c)

	// add a package

	pkg1 := &Package{
		Name:           "some-package-1",
		PackageVersion: "1.2.3",
		CreationInfo:   c,
	}
	pkg2 := &Package{
		Name:           "some-package-2",
		PackageVersion: "2.4.5",
		CreationInfo:   c,
	}
	doc.Elements = append(doc.Elements, pkg2)

	file1 := &File{
		Name:         "/bin/bash",
		CreationInfo: c,
	}
	doc.Elements = append(doc.Elements, file1)

	// add relationships

	doc.Elements = append(doc.Elements,
		&Relationship{
			CreationInfo:     c,
			From:             file1,
			RelationshipType: RelationshipType_Contains,
			To: []IElement{
				pkg1,
				pkg2,
			},
		},
	)

	doc.Elements = append(doc.Elements,
		&Relationship{
			CreationInfo:     c,
			From:             pkg1,
			RelationshipType: RelationshipType_DependsOn,
			To: []IElement{
				pkg2,
			},
		},
	)

	doc.Elements = append(doc.Elements,
		&AIPackage{
			CreationInfo: c,
			TypeOfModel:  []string{"a model"},
		},
	)

	got := encodeDecodeRecode(t, &doc)

	// some basic verification:

	var pkgs []IPackage
	for _, e := range got.GetElements() {
		if rel, ok := e.(IRelationship); ok && rel.GetRelationshipType() == RelationshipType_Contains {
			if from, ok := rel.GetFrom().(IFile); ok && from.GetName() == "/bin/bash" {
				for _, el := range rel.GetTo() {
					if pkg, ok := el.(IPackage); ok {
						pkgs = append(pkgs, pkg)
					}
				}

			}
		}
	}
	if len(pkgs) != 2 {
		t.Error("wrong packages returned")
	}
}

func Test_stringSlice(t *testing.T) {
	p := &AIPackage{
		TypeOfModel: []string{"a model"},
	}
	encodeDecodeRecode(t, p)
}

func Test_profileConformance(t *testing.T) {
	doc := &SpdxDocument{
		ProfileConformance: []ProfileIdentifierType{
			ProfileIdentifierType_Software,
		},
	}
	encodeDecodeRecode(t, doc)
}

func Test_externalID(t *testing.T) {
	doc := &SpdxDocument{
		Elements: []IElement{
			&Element{
				SpdxId: "http://someplace.org/ac7b643f0b2d",
			},
		},
	}
	encodeDecodeRecode(t, doc)
}

// encodeDecodeRecode encodes to JSON, decodes from the JSON, and re-encodes in JSON to validate nothing is lost
func encodeDecodeRecode[T comparable](t *testing.T, obj T) T {
	// serialization:
	maps, err := ldGlobal.toMaps(obj)
	if err != nil {
		t.Fatal(err)
	}

	buf := bytes.Buffer{}
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	err = enc.Encode(maps)
	if err != nil {
		t.Fatal(err)
	}

	json1 := buf.String()
	t.Logf("--------- initial JSON: ----------\n%s\n\n", json1)

	// deserialization:
	graph, err := ldGlobal.FromJSON(strings.NewReader(json1))
	var got T
	for _, entry := range graph {
		if e, ok := entry.(T); ok {
			got = e
			break
		}
	}

	var empty T
	if got == empty {
		t.Fatalf("did not find object in graph, json: %s", json1)
	}

	// re-serialize:
	maps, err = ldGlobal.toMaps(got)
	if err != nil {
		t.Fatal(err)
	}
	buf = bytes.Buffer{}
	enc = json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	err = enc.Encode(maps)
	if err != nil {
		t.Fatal(err)
	}
	json2 := buf.String()
	t.Logf("--------- reserialized JSON: ----------\n%s\n", json2)

	// compare original to parsed and re-encoded

	diff := difflib.UnifiedDiff{
		A:        difflib.SplitLines(json1),
		B:        difflib.SplitLines(json2),
		FromFile: "Original",
		ToFile:   "Current",
		Context:  3,
	}
	text, _ := difflib.GetUnifiedDiffString(diff)
	if text != "" {
		t.Fatal(text)
	}

	return got
}

func Test_refCount(t *testing.T) {
	type O1 struct {
		Name string
	}

	type O2 struct {
		Name string
		O1s  []*O1
	}

	o1 := &O1{"o1"}
	o2 := &O1{"o2"}
	o3 := &O1{"o3"}
	o21 := &O2{"o21", []*O1{o1, o1, o2, o3}}
	o22 := []*O2{
		{"o22-1", []*O1{o1, o1, o1, o1, o2, o3}},
		{"o22-2", []*O1{o1, o1, o1, o1, o2, o3}},
		{"o22-3", []*O1{o1, o1, o1, o1, o2, o3}},
	}

	type O3 struct {
		Name string
		Ref  []*O3
	}
	o31 := &O3{"o31", nil}
	o32 := &O3{"o32", []*O3{o31}}
	o33 := &O3{"o33", []*O3{o32}}
	o31.Ref = []*O3{o33}
	o34 := &O3{"o34", []*O3{o31, o32}}
	o35 := &O3{"o35", []*O3{o31, o32, o31, o32}}

	type O4 struct {
		Name string
		Ref  any
	}
	o41 := &O4{"o41", nil}
	o42 := &O4{"o42", o41}

	tests := []struct {
		name     string
		checkObj any
		checkIn  any
		expected int
	}{
		{
			name:     "none",
			checkObj: o33,
			checkIn:  o21,
			expected: 0,
		},
		{
			name:     "interface",
			checkObj: o41,
			checkIn:  o42,
			expected: 1,
		},
		{
			name:     "single",
			checkObj: o3,
			checkIn:  o21,
			expected: 1,
		},
		{
			name:     "multiple",
			checkObj: o1,
			checkIn:  o21,
			expected: 2,
		},

		{
			name:     "multiple 2",
			checkObj: o1,
			checkIn:  o22,
			expected: 12,
		},
		{
			name:     "circular 1",
			checkObj: o31,
			checkIn:  o31,
			expected: 1,
		},
		{
			name:     "circular 2",
			checkObj: o32,
			checkIn:  o31,
			expected: 1,
		},
		{
			name:     "circular 3",
			checkObj: o33,
			checkIn:  o31,
			expected: 1,
		},
		{
			name:     "circular multiple",
			checkObj: o32,
			checkIn:  o34,
			expected: 2,
		},
		{
			name:     "circular multiple 2",
			checkObj: o32,
			checkIn:  o35,
			expected: 3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cnt := refCount(tt.checkObj, tt.checkIn)
			if cnt != tt.expected {
				t.Errorf("wrong reference count: %v != %v", tt.expected, cnt)
			}
		})
	}
}
