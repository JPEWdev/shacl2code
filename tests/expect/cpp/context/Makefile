CXX=g++
CPPFLAGS=
CXXFLAGS=
LDFLAGS=
AR=ar
LD=ld
INSTALL=install
PREFIX=/usr/local/
DESTDIR=
COPY=cp

LIB_OBJS = datetime.o decode.o encode.o errorhandler.o extensible.o link.o namedindividual.o object.o objectpath.o objectset.o property.o propertyvalue.o refproperty.o type.o util.o test-context.o test-context-jsonld.o

VALIDATE_OBJS = test-context-validate.o
ALL_OBJS = $(LIB_OBJS) $(VALIDATE_OBJS)

all: libtest-context.so libtest-context.a test-context-validate docs

clean:
	rm -rf *.o *.so *.a test-context-validate doc/

install: libtest-context.so libtest-context.a docs
	# Library
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/lib
	$(INSTALL) -m 0755 libtest-context.so $(DESTDIR)/$(PREFIX)/lib/libtest-context.so.0.0.16
	ln -s libtest-context.so.0.0.16 $(DESTDIR)/$(PREFIX)/lib/libtest-context.so
	ln -s libtest-context.so.0.0.16 $(DESTDIR)/$(PREFIX)/lib/libtest-context.so.0

	$(INSTALL) -m 0644 libtest-context.a $(DESTDIR)/$(PREFIX)/lib/

	# Package Config
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/lib/pkgconfig

	$(INSTALL) -m 0644 test-context.pc $(DESTDIR)/$(PREFIX)/lib/pkgconfig/
	sed -i -e 's^@@PREFIX@@^$(PREFIX)^g' \
		$(DESTDIR)/$(PREFIX)/lib/pkgconfig/test-context.pc

	# Headers
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/include/test-context
	$(INSTALL) -m 0644 api.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 datetime.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 decode.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 encode.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 errorhandler.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 exceptions.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 extensible.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 link.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 namedindividual.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 object.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 objectpath.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 objectset.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 prop.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 property.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 propertyvalue.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 ref.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 refproperty.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 type.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 util.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 walk.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 test-context.hpp $(DESTDIR)/$(PREFIX)/include/test-context/
	$(INSTALL) -m 0644 test-context-jsonld.hpp $(DESTDIR)/$(PREFIX)/include/test-context/

	# Binaries
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/bin

	$(INSTALL) -m 0755 test-context-validate $(DESTDIR)/$(PREFIX)/bin/

	# Documentation
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/share/doc/libtest-context
	$(COPY) -dR doc/ $(DESTDIR)/$(PREFIX)/share/doc/libtest-context/

%.o: %.cpp
	@echo " [CC]  $<"
	$(CXX) -c -o $@ $< $(CPPFLAGS) $(CXXFLAGS) \
		-fPIC \
		-fvisibility=hidden \
		-fvisibility-inlines-hidden \
		-DSHACL2CODE_TEST_CONTEXT_DLL=1 \
		-DSHACL2CODE_TEST_CONTEXT_DLL_EXPORT=1

libtest-context.a: $(LIB_OBJS)
	# Combine all object files into a single object file. This is required
	# otherwise the linker may only include object files that were actually
	# referenced and the initializers will not run
	@echo " [LD]  libtest-context.static.o"
	$(LD) -relocatable -o libtest-context.static.o $^
	@echo " [AR]  $@"
	$(AR) rcs $@ libtest-context.static.o

libtest-context.so: $(LIB_OBJS)
	@echo " [LD]  $@"
	$(CXX) -shared -fPIC -Wl,-soname,libtest-context.so.0 $(LDFLAGS) -o $@ $^

test-context-validate: $(VALIDATE_OBJS) libtest-context.a
	@echo " [LD]  $@"
	$(CXX) $(LDFLAGS) -o $@ $^

docs:
	@echo " [DOC]"
	doxygen

# Use `make V=1` to print commands.
$(V).SILENT:

.PHONY: clean all docs

