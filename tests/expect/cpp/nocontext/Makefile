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

LIB_OBJS = datetime.o decode.o encode.o errorhandler.o extensible.o link.o namedindividual.o object.o objectpath.o objectset.o property.o propertyvalue.o refproperty.o type.o util.o test.o test-jsonld.o

VALIDATE_OBJS = test-validate.o
ALL_OBJS = $(LIB_OBJS) $(VALIDATE_OBJS)

all: libtest.so libtest.a test-validate docs

clean:
	rm -rf *.o *.so *.a test-validate doc/

install: libtest.so libtest.a docs
	# Library
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/lib
	$(INSTALL) -m 0755 libtest.so $(DESTDIR)/$(PREFIX)/lib/libtest.so.0.0.16
	ln -s libtest.so.0.0.16 $(DESTDIR)/$(PREFIX)/lib/libtest.so
	ln -s libtest.so.0.0.16 $(DESTDIR)/$(PREFIX)/lib/libtest.so.0

	$(INSTALL) -m 0644 libtest.a $(DESTDIR)/$(PREFIX)/lib/

	# Package Config
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/lib/pkgconfig

	$(INSTALL) -m 0644 test.pc $(DESTDIR)/$(PREFIX)/lib/pkgconfig/
	sed -i -e 's^@@PREFIX@@^$(PREFIX)^g' \
		$(DESTDIR)/$(PREFIX)/lib/pkgconfig/test.pc

	# Headers
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/include/test
	$(INSTALL) -m 0644 api.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 datetime.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 decode.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 encode.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 errorhandler.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 exceptions.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 extensible.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 link.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 namedindividual.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 object.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 objectpath.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 objectset.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 prop.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 property.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 propertyvalue.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 ref.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 refproperty.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 type.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 util.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 walk.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 test.hpp $(DESTDIR)/$(PREFIX)/include/test/
	$(INSTALL) -m 0644 test-jsonld.hpp $(DESTDIR)/$(PREFIX)/include/test/

	# Binaries
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/bin

	$(INSTALL) -m 0755 test-validate $(DESTDIR)/$(PREFIX)/bin/

	# Documentation
	$(INSTALL) -d $(DESTDIR)/$(PREFIX)/share/doc/libtest
	$(COPY) -dR doc/ $(DESTDIR)/$(PREFIX)/share/doc/libtest/

%.o: %.cpp
	@echo " [CC]  $<"
	$(CXX) -c -o $@ $< $(CPPFLAGS) $(CXXFLAGS) \
		-fPIC \
		-fvisibility=hidden \
		-fvisibility-inlines-hidden \
		-DSHACL2CODE_TEST_DLL=1 \
		-DSHACL2CODE_TEST_DLL_EXPORT=1

libtest.a: $(LIB_OBJS)
	# Combine all object files into a single object file. This is required
	# otherwise the linker may only include object files that were actually
	# referenced and the initializers will not run
	@echo " [LD]  libtest.static.o"
	$(LD) -relocatable -o libtest.static.o $^
	@echo " [AR]  $@"
	$(AR) rcs $@ libtest.static.o

libtest.so: $(LIB_OBJS)
	@echo " [LD]  $@"
	$(CXX) -shared -fPIC -Wl,-soname,libtest.so.0 $(LDFLAGS) -o $@ $^

test-validate: $(VALIDATE_OBJS) libtest.a
	@echo " [LD]  $@"
	$(CXX) $(LDFLAGS) -o $@ $^

docs:
	@echo " [DOC]"
	doxygen

# Use `make V=1` to print commands.
$(V).SILENT:

.PHONY: clean all docs

