# note, parametrised macros are order-senisitve (unlike not-parametrized) even with normal macros
# also necessary when passing it as parameter other macros. If not macro, then it is considered as switch
%global debug_suffix_unquoted -debug
# quoted one for shell operations
%global debug_suffix "%{debug_suffix_unquoted}"
%global normal_suffix ""

#if you wont only debug build, but providing java, build only normal build, but  set normalbuild_parameter
%global debugbuild_parameter  slowdebug
%global normalbuild_parameter release
%global debug_warning This package have full debug on. Install only in need, and remove asap.
%global debug_on with full debug on
%global for_debug for packages with debug on

# by default we build normal build always.
%global include_normal_build 1
%if %{include_normal_build}
%global build_loop1 %{normal_suffix}
%else
%global build_loop1 %{nil}
%endif

%global aarch64         aarch64 arm64 armv8
# sometimes we need to distinguish big and little endian PPC64
%global ppc64le         ppc64le
%global ppc64be         ppc64 ppc64p7
%global multilib_arches %{power64} sparc64 x86_64
%global jit_arches      %{ix86} x86_64 sparcv9 sparc64 %{aarch64} %{power64}
%global shipped_jits    %{ix86} x86_64

# By default, we build a debug build during main build on shipped JIT architectures
%ifarch %{shipped_jits}
%global include_debug_build 1
%else
%global include_debug_build 0
%endif

%if %{include_debug_build}
%global build_loop2 %{debug_suffix}
%else
%global build_loop2 %{nil}
%endif

# if you disable both builds, then build fails
%global build_loop  %{build_loop1} %{build_loop2}
# note, that order  normal_suffix debug_suffix, in case of both enabled,
# is expected in one single case at the end of build
%global rev_build_loop  %{build_loop2} %{build_loop1}

%ifarch %{jit_arches}
%global bootstrap_build 1
%else
%global bootstrap_build 0
%endif

%if %{bootstrap_build}
%global targets bootcycle-images docs
%else
%global targets all
%endif

# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimisation of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wformat (required by -Werror=format-security)
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%global ourflags %(echo %optflags | sed -e 's|-Wall|-Wformat|' | sed -r -e 's|-O[0-9]*||')
%global ourcppflags %(echo %ourflags | sed -e 's|-fexceptions||' | sed -e 's|-fasynchronous-unwind-tables||')
# no __global_ldflags in RHEL 6
%global ourldflags %{nil}

# With diabled nss is NSS deactivated, so in NSS_LIBDIR can be wrong path
# the initialisation must be here. LAter the pkg-connfig have bugy behaviour
#looks liekopenjdk RPM specific bug
# Always set this so the nss.cfg file is not broken
%global NSS_LIBDIR %(pkg-config --variable=libdir nss)
%global NSS_LIBS %(pkg-config --libs nss)
%global NSS_CFLAGS %(pkg-config --cflags nss-softokn)
# see https://bugzilla.redhat.com/show_bug.cgi?id=1332456
%global NSSSOFTOKN_BUILDTIME_NUMBER %(pkg-config --modversion nss-softokn || : )
%global NSS_BUILDTIME_NUMBER %(pkg-config --modversion nss || : )
#this is worakround for processing of requires during srpm creation
%global NSSSOFTOKN_BUILDTIME_VERSION %(if [ "x%{NSSSOFTOKN_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSSSOFTOKN_BUILDTIME_NUMBER}" ;fi)
%global NSS_BUILDTIME_VERSION %(if [ "x%{NSS_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSS_BUILDTIME_NUMBER}" ;fi)


# Fix for https://bugzilla.redhat.com/show_bug.cgi?id=1111349.
# See also https://bugzilla.redhat.com/show_bug.cgi?id=1590796
# as to why some libraries *cannot* be excluded. In particular,
# these are:
# libjsig.so, libjava.so, libjawt.so, libjvm.so and libverify.so
%global _privatelibs libatk-wrapper[.]so.*|libattach[.]so.*|libawt_headless[.]so.*|libawt[.]so.*|libawt_xawt[.]so.*|libdt_socket[.]so.*|libfontmanager[.]so.*|libhprof[.]so.*|libinstrument[.]so.*|libj2gss[.]so.*|libj2pcsc[.]so.*|libj2pkcs11[.]so.*|libjaas_unix[.]so.*|libjava_crw_demo[.]so.*|libjavajpeg[.]so.*|libjdwp[.]so.*|libjli[.]so.*|libjsdt[.]so.*|libjsoundalsa[.]so.*|libjsound[.]so.*|liblcms[.]so.*|libmanagement[.]so.*|libmlib_image[.]so.*|libnet[.]so.*|libnio[.]so.*|libnpt[.]so.*|libsaproc[.]so.*|libsctp[.]so.*|libsplashscreen[.]so.*|libsunec[.]so.*|libunpack[.]so.*|libzip[.]so.*|lib[.]so\\(SUNWprivate_.*

%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

%ifarch x86_64
%global archinstall amd64
%endif
%ifarch ppc
%global archinstall ppc
%endif
%ifarch %{ppc64be}
%global archinstall ppc64
%endif
%ifarch %{ppc64le}
%global archinstall ppc64le
%endif
%ifarch %{ix86}
%global archinstall i386
%endif
%ifarch ia64
%global archinstall ia64
%endif
%ifarch s390
%global archinstall s390
%endif
%ifarch s390x
%global archinstall s390x
%endif
%ifarch %{arm}
%global archinstall arm
%endif
%ifarch %{aarch64}
%global archinstall aarch64
%endif
# 32 bit sparc, optimized for v9
%ifarch sparcv9
%global archinstall sparc
%endif
# 64 bit sparc
%ifarch sparc64
%global archinstall sparcv9
%endif
%ifnarch %{jit_arches}
%global archinstall %{_arch}
%endif

%ifarch %{jit_arches}
%global with_systemtap 1
%else
%global with_systemtap 0
%endif

# Convert an absolute path to a relative path.  Each symbolic link is
# specified relative to the directory in which it is installed so that
# it will resolve properly within chrooted installations.
%global script 'use File::Spec; print File::Spec->abs2rel($ARGV[0], $ARGV[1])'
%global abs2rel %{__perl} -e %{script}


# Standard JPackage naming and versioning defines.
%global origin          openjdk
%global top_level_dir_name   %{origin}
# note, following three variables are sedded from update_sources if used correctly. Hardcode them rather there.
%global shenandoah_project	aarch64-port
%global shenandoah_repo		jdk8u-shenandoah
%global shenandoah_revision    	aarch64-shenandoah-jdk8u212-b04
# Define old aarch64/jdk8u tree variables for compatibility
%global project         %{shenandoah_project}
%global repo            %{shenandoah_repo}
%global revision        %{shenandoah_revision}

# eg # jdk8u60-b27 -> jdk8u60 or # aarch64-jdk8u60-b27 -> aarch64-jdk8u60  (dont forget spec escape % by %%)
%global whole_update    %(VERSION=%{revision}; echo ${VERSION%%-*})
# eg  jdk8u60 -> 60 or aarch64-jdk8u60 -> 60
%global updatever       %(VERSION=%{whole_update}; echo ${VERSION##*u})
# eg jdk8u60-b27 -> b27
%global buildver        %(VERSION=%{revision}; echo ${VERSION##*-})
# priority must be 7 digits in total. The expression is workarounding tip
%global priority        %(TIP=1800%{updatever};  echo ${TIP/tip/999})

%global javaver         1.8.0

# parametrized macros are order-sensitive
%global fullversion     %{name}-%{version}-%{release}
#images stub
%global j2sdkimage       j2sdk-image
# output dir stub
%global buildoutputdir() %{expand:%{top_level_dir_name}/build/jdk8.build%1}
#we can copy the javadoc to not arched dir, or made it not noarch
%global uniquejavadocdir()    %{expand:%{fullversion}%1}
#main id and dir of this jdk
%global uniquesuffix()        %{expand:%{fullversion}.%{_arch}%1}

# Standard JPackage directories and symbolic links.
%global sdkdir()        %{expand:%{uniquesuffix %%1}}
%global jrelnk()        %{expand:jre-%{javaver}-%{origin}-%{version}-%{release}.%{_arch}%1}

#rhel 6 only fix for https://bugzilla.redhat.com/show_bug.cgi?id=1217177
#this is breakng multipleinstalls
%global sdk_versionless_lnk()        %{expand:%{_jvmdir}/java-%{javaver}-%{origin}.%{_arch}%1}
%global jre_versionless_lnk()        %{expand:%{_jvmdir}/jre-%{javaver}-%{origin}.%{_arch}%1}
#first is link to not-macroed sdkbindir (usage of macro makes alternatives inconsistent again)
#second is link to not-macroed jrebindir
#those are created somewhere during install and used in alternatives later
#end of fix of rhbz#1217177 (but see creation and alternatives)


%global jredir()        %{expand:%{sdkdir %%1}/jre}
%global sdkbindir()     %{expand:%{_jvmdir}/%{sdkdir %%1}/bin}
%global jrebindir()     %{expand:%{_jvmdir}/%{jredir %%1}/bin}
%global jvmjardir()     %{expand:%{_jvmjardir}/%{uniquesuffix %%1}}

%global rpm_state_dir %{_localstatedir}/lib/rpm-state/

#another hunk needed by fix for 1217177
%global jardir_jre() %{expand:
%{_jvmjardir}/jre-%{javaver}-%{origin}.%{_arch}%1
}
%global jardir_sdk() %{expand:
%{_jvmjardir}/java-%{javaver}-%{origin}.%{_arch}%1
}
#end of naother hunk

%if %{with_systemtap}
# Where to install systemtap tapset (links)
# We would like these to be in a package specific subdir,
# but currently systemtap doesn't support that, so we have to
# use the root tapset dir for now. To distinquish between 64
# and 32 bit architectures we place the tapsets under the arch
# specific dir (note that systemtap will only pickup the tapset
# for the primary arch for now). Systemtap uses the machine name
# aka build_cpu as architecture specific directory name.
%global tapsetroot /usr/share/systemtap
%global tapsetdir %{tapsetroot}/tapset/%{_build_cpu}
%endif

# not-duplicated scriplets for normal/debug packages
%global update_desktop_icons /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :


%global post_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
exit 0
}


%global post_headless() %{expand:
# FIXME: identical binaries are copied, not linked. This needs to be
# fixed upstream.
%ifarch %{jit_arches}
# MetaspaceShared::generate_vtable_methods not implemented for PPC JIT
%ifnarch %{power64}
#see https://bugzilla.redhat.com/show_bug.cgi?id=513605
%{jrebindir %%1}/java -Xshare:dump >/dev/null 2>/dev/null
%endif
%endif

PRIORITY=%{priority}
if [ "%1" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
alternatives \\
  --install %{_bindir}/java java %{jre_versionless_lnk %%1}/bin/java $PRIORITY \\
  --slave %{_jvmdir}/jre jre %{_jvmdir}/%{jredir %%1} \\
  --slave %{_jvmjardir}/jre jre_exports %{_jvmjardir}/%{jrelnk %%1} \\
  --slave %{_bindir}/jjs jjs %{jrebindir %%1}/jjs \\
  --slave %{_bindir}/keytool keytool %{jrebindir %%1}/keytool \\
  --slave %{_bindir}/orbd orbd %{jrebindir %%1}/orbd \\
  --slave %{_bindir}/pack200 pack200 %{jrebindir %%1}/pack200 \\
  --slave %{_bindir}/rmid rmid %{jrebindir %%1}/rmid \\
  --slave %{_bindir}/rmiregistry rmiregistry %{jrebindir %%1}/rmiregistry \\
  --slave %{_bindir}/servertool servertool %{jrebindir %%1}/servertool \\
  --slave %{_bindir}/tnameserv tnameserv %{jrebindir %%1}/tnameserv \\
  --slave %{_bindir}/policytool policytool %{jrebindir %%1}/policytool \\
  --slave %{_bindir}/unpack200 unpack200 %{jrebindir %%1}/unpack200 \\
  --slave %{_mandir}/man1/java.1$ext java.1$ext \\
  %{_mandir}/man1/java-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jjs.1$ext jjs.1$ext \\
  %{_mandir}/man1/jjs-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/keytool.1$ext keytool.1$ext \\
  %{_mandir}/man1/keytool-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/orbd.1$ext orbd.1$ext \\
  %{_mandir}/man1/orbd-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/pack200.1$ext pack200.1$ext \\
  %{_mandir}/man1/pack200-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/rmid.1$ext rmid.1$ext \\
  %{_mandir}/man1/rmid-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/rmiregistry.1$ext rmiregistry.1$ext \\
  %{_mandir}/man1/rmiregistry-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/servertool.1$ext servertool.1$ext \\
  %{_mandir}/man1/servertool-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/tnameserv.1$ext tnameserv.1$ext \\
  %{_mandir}/man1/tnameserv-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/policytool.1$ext policytool.1$ext \\
  %{_mandir}/man1/policytool-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/unpack200.1$ext unpack200.1$ext \\
  %{_mandir}/man1/unpack200-%{uniquesuffix %%1}.1$ext

for X in %{origin} %{javaver} ; do
  alternatives \\
    --install %{_jvmdir}/jre-"$X" \\
    jre_"$X" %{_jvmdir}/%{jredir %%1} $PRIORITY \\
    --slave %{_jvmjardir}/jre-"$X" \\
    jre_"$X"_exports %{_jvmdir}/%{jredir %%1}
done

#update-alternatives --install %{_jvmdir}/jre-%{javaver}-%{origin} jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk %%1} $PRIORITY \\
#--slave %{_jvmjardir}/jre-%{javaver}-%{origin}       jre_%{javaver}_%{origin}_exports      %{jvmjardir %%1}
#removed in favor of hardcoded link rhbnz#1217177

update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

# see pretrans where this file is declared
# also see that pretrans is only for nondebug
if [ ! "%1" == %{debug_suffix} ]; then
  if [ -f %{_libexecdir}/copy_jdk_configs_fixFiles.sh ] ; then
    sh  %{_libexecdir}/copy_jdk_configs_fixFiles.sh %{rpm_state_dir}/%{name}.%{_arch}  %{_jvmdir}/%{sdkdir %%1}
  fi
fi

exit 0
}

%global postun_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}


%global postun_headless() %{expand:
# now using versionless symlink here, part of rhbnz#1217177
if [ $1 -eq 0 ]
then
  alternatives --remove java %{jre_versionless_lnk %%1}/bin/java
fi
  alternatives --remove jre_%{origin} %{_jvmdir}/%{jredir %%1}
  alternatives --remove jre_%{javaver} %{_jvmdir}/%{jredir %%1}
# removed in favour of rhbnz#1217177
#  alternatives --remove jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk %%1}
}

%global posttrans_script() %{expand:
%{update_desktop_icons}
}

%global post_devel() %{expand:

PRIORITY=%{priority}
if [ "%1" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
alternatives \\
  --install %{_bindir}/javac javac %{sdk_versionless_lnk %%1}/bin/javac $PRIORITY \\
  --slave %{_jvmdir}/java java_sdk %{_jvmdir}/%{sdkdir %%1} \\
  --slave %{_jvmjardir}/java java_sdk_exports %{_jvmjardir}/%{sdkdir %%1} \\
  --slave %{_bindir}/appletviewer appletviewer %{sdkbindir %%1}/appletviewer \\
  --slave %{_bindir}/extcheck extcheck %{sdkbindir %%1}/extcheck \\
  --slave %{_bindir}/idlj idlj %{sdkbindir %%1}/idlj \\
  --slave %{_bindir}/jar jar %{sdkbindir %%1}/jar \\
  --slave %{_bindir}/jarsigner jarsigner %{sdkbindir %%1}/jarsigner \\
  --slave %{_bindir}/javadoc javadoc %{sdkbindir %%1}/javadoc \\
  --slave %{_bindir}/javah javah %{sdkbindir %%1}/javah \\
  --slave %{_bindir}/javap javap %{sdkbindir %%1}/javap \\
  --slave %{_bindir}/jcmd jcmd %{sdkbindir %%1}/jcmd \\
  --slave %{_bindir}/jconsole jconsole %{sdkbindir %%1}/jconsole \\
  --slave %{_bindir}/jdb jdb %{sdkbindir %%1}/jdb \\
  --slave %{_bindir}/jdeps jdeps %{sdkbindir %%1}/jdeps \\
  --slave %{_bindir}/jhat jhat %{sdkbindir %%1}/jhat \\
  --slave %{_bindir}/jinfo jinfo %{sdkbindir %%1}/jinfo \\
  --slave %{_bindir}/jmap jmap %{sdkbindir %%1}/jmap \\
  --slave %{_bindir}/jps jps %{sdkbindir %%1}/jps \\
  --slave %{_bindir}/jrunscript jrunscript %{sdkbindir %%1}/jrunscript \\
  --slave %{_bindir}/jsadebugd jsadebugd %{sdkbindir %%1}/jsadebugd \\
  --slave %{_bindir}/jstack jstack %{sdkbindir %%1}/jstack \\
  --slave %{_bindir}/jstat jstat %{sdkbindir %%1}/jstat \\
  --slave %{_bindir}/jstatd jstatd %{sdkbindir %%1}/jstatd \\
  --slave %{_bindir}/native2ascii native2ascii %{sdkbindir %%1}/native2ascii \\
  --slave %{_bindir}/rmic rmic %{sdkbindir %%1}/rmic \\
  --slave %{_bindir}/schemagen schemagen %{sdkbindir %%1}/schemagen \\
  --slave %{_bindir}/serialver serialver %{sdkbindir %%1}/serialver \\
  --slave %{_bindir}/wsgen wsgen %{sdkbindir %%1}/wsgen \\
  --slave %{_bindir}/wsimport wsimport %{sdkbindir %%1}/wsimport \\
  --slave %{_bindir}/xjc xjc %{sdkbindir %%1}/xjc \\
  --slave %{_mandir}/man1/appletviewer.1$ext appletviewer.1$ext \\
  %{_mandir}/man1/appletviewer-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/extcheck.1$ext extcheck.1$ext \\
  %{_mandir}/man1/extcheck-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/idlj.1$ext idlj.1$ext \\
  %{_mandir}/man1/idlj-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jar.1$ext jar.1$ext \\
  %{_mandir}/man1/jar-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jarsigner.1$ext jarsigner.1$ext \\
  %{_mandir}/man1/jarsigner-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/javac.1$ext javac.1$ext \\
  %{_mandir}/man1/javac-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/javadoc.1$ext javadoc.1$ext \\
  %{_mandir}/man1/javadoc-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/javah.1$ext javah.1$ext \\
  %{_mandir}/man1/javah-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/javap.1$ext javap.1$ext \\
  %{_mandir}/man1/javap-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jcmd.1$ext jcmd.1$ext \\
  %{_mandir}/man1/jcmd-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jconsole.1$ext jconsole.1$ext \\
  %{_mandir}/man1/jconsole-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jdb.1$ext jdb.1$ext \\
  %{_mandir}/man1/jdb-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jdeps.1$ext jdeps.1$ext \\
  %{_mandir}/man1/jdeps-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jhat.1$ext jhat.1$ext \\
  %{_mandir}/man1/jhat-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jinfo.1$ext jinfo.1$ext \\
  %{_mandir}/man1/jinfo-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jmap.1$ext jmap.1$ext \\
  %{_mandir}/man1/jmap-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jps.1$ext jps.1$ext \\
  %{_mandir}/man1/jps-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jrunscript.1$ext jrunscript.1$ext \\
  %{_mandir}/man1/jrunscript-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jsadebugd.1$ext jsadebugd.1$ext \\
  %{_mandir}/man1/jsadebugd-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jstack.1$ext jstack.1$ext \\
  %{_mandir}/man1/jstack-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jstat.1$ext jstat.1$ext \\
  %{_mandir}/man1/jstat-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/jstatd.1$ext jstatd.1$ext \\
  %{_mandir}/man1/jstatd-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/native2ascii.1$ext native2ascii.1$ext \\
  %{_mandir}/man1/native2ascii-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/rmic.1$ext rmic.1$ext \\
  %{_mandir}/man1/rmic-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/schemagen.1$ext schemagen.1$ext \\
  %{_mandir}/man1/schemagen-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/serialver.1$ext serialver.1$ext \\
  %{_mandir}/man1/serialver-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/wsgen.1$ext wsgen.1$ext \\
  %{_mandir}/man1/wsgen-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/wsimport.1$ext wsimport.1$ext \\
  %{_mandir}/man1/wsimport-%{uniquesuffix %%1}.1$ext \\
  --slave %{_mandir}/man1/xjc.1$ext xjc.1$ext \\
  %{_mandir}/man1/xjc-%{uniquesuffix %%1}.1$ext

for X in %{origin} %{javaver} ; do
  alternatives \\
    --install %{_jvmdir}/java-"$X" \\
    java_sdk_"$X" %{_jvmdir}/%{sdkdir %%1} $PRIORITY  \\
    --slave %{_jvmjardir}/java-"$X" \\
    java_sdk_"$X"_exports %{_jvmjardir}/%{sdkdir %%1}
done

#update-alternatives --install %{_jvmdir}/java-%{javaver}-%{origin} java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir %%1} $PRIORITY  \\
#--slave %{_jvmjardir}/java-%{javaver}-%{origin}       java_sdk_%{javaver}_%{origin}_exports      %{_jvmjardir}/%{sdkdir %%1}
#removed in favor of hardcoded link rhbnz#1217177

update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

exit 0
}

%global postun_devel() %{expand:
# now using versionless symlink here, part of rhbnz#1217177
if [ $1 -eq 0 ]
then
  alternatives --remove javac %{sdk_versionless_lnk %%1}/bin/javac
fi
  alternatives --remove java_sdk_%{origin} %{_jvmdir}/%{sdkdir %%1}
  alternatives --remove java_sdk_%{javaver} %{_jvmdir}/%{sdkdir %%1}
# removed in favour of rhbnz#1217177
#  alternatives --remove java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir %%1}

update-desktop-database %{_datadir}/applications &> /dev/null || :

if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}

%global posttrans_devel() %{expand:
%{update_desktop_icons}
}

%global post_javadoc() %{expand:

PRIORITY=%{priority}
if [ "%1" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

alternatives \\
  --install %{_javadocdir}/java javadocdir %{_javadocdir}/%{uniquejavadocdir %%1}/api \\
  $PRIORITY
exit 0
}

%global postun_javadoc() %{expand:
  alternatives --remove javadocdir %{_javadocdir}/%{uniquejavadocdir %%1}/api
exit 0
}

%global files_jre() %{expand:
%{_datadir}/icons/hicolor/*x*/apps/java-%{javaver}.png
%{_datadir}/applications/*policytool%1.desktop
}


%global files_jre_headless() %{expand:
%defattr(-,root,root,-)
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/jre/ASSEMBLY_EXCEPTION
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/jre/LICENSE
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/jre/THIRD_PARTY_README
%dir %{_jvmdir}/%{sdkdir %%1}
#two rhel 6 only dir rhbz#1217177
%dir %{jre_versionless_lnk %%1}
%dir %{jardir_jre %%1}
%{_jvmdir}/%{jrelnk %%1}
%{_jvmjardir}/%{jrelnk %%1}
%{_jvmprivdir}/*
%{jvmjardir %%1}
%dir %{_jvmdir}/%{jredir %%1}/lib/security
%{_jvmdir}/%{jredir %%1}/lib/security/cacerts
%dir %{_jvmdir}/%{jredir %%1}/lib/security/policy/unlimited/
%dir %{_jvmdir}/%{jredir %%1}/lib/security/policy/limited/
%dir %{_jvmdir}/%{jredir %%1}/lib/security/policy/
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/policy/unlimited/US_export_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/policy/unlimited/local_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/policy/limited/US_export_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/policy/limited/local_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/java.policy
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/java.security
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/blacklisted.certs
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/logging.properties
%{_mandir}/man1/java-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jjs-%{uniquesuffix %%1}.1*
%{_mandir}/man1/keytool-%{uniquesuffix %%1}.1*
%{_mandir}/man1/orbd-%{uniquesuffix %%1}.1*
%{_mandir}/man1/pack200-%{uniquesuffix %%1}.1*
%{_mandir}/man1/rmid-%{uniquesuffix %%1}.1*
%{_mandir}/man1/rmiregistry-%{uniquesuffix %%1}.1*
%{_mandir}/man1/servertool-%{uniquesuffix %%1}.1*
%{_mandir}/man1/tnameserv-%{uniquesuffix %%1}.1*
%{_mandir}/man1/unpack200-%{uniquesuffix %%1}.1*
%{_mandir}/man1/policytool-%{uniquesuffix %%1}.1*
%config(noreplace) %{_jvmdir}/%{jredir %%1}/lib/security/nss.cfg
%ifarch %{jit_arches}
%ifnarch %{power64}
%attr(444, root, root) %ghost %{_jvmdir}/%{jredir %%1}/lib/%{archinstall}/server/classes.jsa
%attr(444, root, root) %ghost %{_jvmdir}/%{jredir %%1}/lib/%{archinstall}/client/classes.jsa
%endif
%endif
%{_jvmdir}/%{jredir %%1}/lib/%{archinstall}/server/
%{_jvmdir}/%{jredir %%1}/lib/%{archinstall}/client/
}

%global files_devel() %{expand:
%defattr(-,root,root,-)
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/ASSEMBLY_EXCEPTION
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/LICENSE
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/THIRD_PARTY_README
%dir %{_jvmdir}/%{sdkdir %%1}/bin
%dir %{_jvmdir}/%{sdkdir %%1}/include
%dir %{_jvmdir}/%{sdkdir %%1}/lib
#two rhel 6 only dir rhbz#1217177
%dir %{sdk_versionless_lnk %%1}
%dir %{jardir_sdk %%1}
%{_jvmdir}/%{sdkdir %%1}/bin/*
%{_jvmdir}/%{sdkdir %%1}/include/*
%{_jvmdir}/%{sdkdir %%1}/lib/*
%{_jvmjardir}/%{sdkdir %%1}
%{_datadir}/applications/*jconsole%1.desktop
%{_mandir}/man1/appletviewer-%{uniquesuffix %%1}.1*
%{_mandir}/man1/extcheck-%{uniquesuffix %%1}.1*
%{_mandir}/man1/idlj-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jar-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jarsigner-%{uniquesuffix %%1}.1*
%{_mandir}/man1/javac-%{uniquesuffix %%1}.1*
%{_mandir}/man1/javadoc-%{uniquesuffix %%1}.1*
%{_mandir}/man1/javah-%{uniquesuffix %%1}.1*
%{_mandir}/man1/javap-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jconsole-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jcmd-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jdb-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jdeps-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jhat-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jinfo-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jmap-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jps-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jrunscript-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jsadebugd-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jstack-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jstat-%{uniquesuffix %%1}.1*
%{_mandir}/man1/jstatd-%{uniquesuffix %%1}.1*
%{_mandir}/man1/native2ascii-%{uniquesuffix %%1}.1*
%{_mandir}/man1/rmic-%{uniquesuffix %%1}.1*
%{_mandir}/man1/schemagen-%{uniquesuffix %%1}.1*
%{_mandir}/man1/serialver-%{uniquesuffix %%1}.1*
%{_mandir}/man1/wsgen-%{uniquesuffix %%1}.1*
%{_mandir}/man1/wsimport-%{uniquesuffix %%1}.1*
%{_mandir}/man1/xjc-%{uniquesuffix %%1}.1*
%if %{with_systemtap}
%dir %{tapsetroot}
%dir %{tapsetdir}
%{tapsetdir}/*%{version}-%{release}.%{_arch}%1.stp
%dir %{_jvmdir}/%{sdkdir %%1}/tapset
%{_jvmdir}/%{sdkdir %%1}/tapset/*.stp
%endif
}

%global files_demo() %{expand:
%defattr(-,root,root,-)
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/jre/LICENSE
}

%global files_src() %{expand:
%defattr(-,root,root,-)
%doc README.src
%{_jvmdir}/%{sdkdir %%1}/src.zip
}

%global files_javadoc() %{expand:
%defattr(-,root,root,-)
%doc %{_javadocdir}/%{uniquejavadocdir %%1}
%doc %{buildoutputdir %%1}/images/%{j2sdkimage}/jre/LICENSE
}


# not-duplicated requires/provides/obsolate for normal/debug packages
%global java_rpo() %{expand:
Requires: fontconfig
Requires: xorg-x11-fonts-Type1

# RHEL 6 only builds on x86, x86_64 and ppc64be (unshipped)
ExclusiveArch: x86_64 i686 %{ppc64be}

# Requires rest of java
Requires: %{name}-headless%1 = %{epoch}:%{version}-%{release}
# for java-X-openjdk package's desktop binding
Requires: gtk2%{?_isa}

# Standard JPackage base provides.
Provides: jre-%{javaver}-%{origin}%1 = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}%1 = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}%1 = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}%1 = %{epoch}:%{version}-%{release}
Provides: jre = %{javaver}%1
Provides: java-%{origin}%1 = %{epoch}:%{version}-%{release}
Provides: java%1 = %{epoch}:%{javaver}
# Standard JPackage extensions provides.
Provides: java-fonts%1 = %{epoch}:%{version}

#Obsoletes: java-1.7.0-openjdk%1
#Obsoletes: java-1.5.0-gcj%1
#Obsoletes: sinjdoc
}

%global java_headless_rpo() %{expand:
# Require /etc/pki/java/cacerts.
Requires: ca-certificates
# Require jpackage-utils for ownership of /usr/lib/jvm/
Requires: jpackage-utils
# Require zoneinfo data provided by tzdata-java subpackage.
Requires: tzdata-java >= 2014f-1
# Part of NSS is statically linked into the libsunec.so library
# so we need at least the version we built against to be available
# on the system. Otherwise, the SunEC provider fails to initialise.
Requires: nss %{NSS_BUILDTIME_VERSION}
Requires: nss-softokn %{NSSSOFTOKN_BUILDTIME_VERSION}
# Post requires alternatives to install tool alternatives.
Requires(post):   %{_sbindir}/alternatives
# Postun requires alternatives to uninstall tool alternatives.
Requires(postun): %{_sbindir}/alternatives
# for optional support of kernel stream control, card reader and printing bindings
Requires: lksctp-tools%{?_isa}, pcsc-lite-libs%{?_isa}, cups-libs%{?_isa}

# Standard JPackage base provides.
Provides: jre-%{javaver}-%{origin}-headless%1 = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}-headless%1 = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}-headless%1 = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-headless%1 = %{epoch}:%{version}-%{release}
Provides: jre-headless%1 = %{epoch}:%{javaver}
Provides: java-%{origin}-headless%1 = %{epoch}:%{version}-%{release}
Provides: java-headless%1 = %{epoch}:%{javaver}
# Standard JPackage extensions provides.
Provides: jndi%1 = %{epoch}:%{version}
Provides: jndi-ldap%1 = %{epoch}:%{version}
Provides: jndi-cos%1 = %{epoch}:%{version}
Provides: jndi-rmi%1 = %{epoch}:%{version}
Provides: jndi-dns%1 = %{epoch}:%{version}
Provides: jaas%1 = %{epoch}:%{version}
Provides: jsse%1 = %{epoch}:%{version}
Provides: jce%1 = %{epoch}:%{version}
Provides: jdbc-stdext%1 = 4.1
Provides: java-sasl%1 = %{epoch}:%{version}

#Obsoletes: java-1.7.0-openjdk-headless%1
}

%global java_devel_rpo() %{expand:
# Require base package.
Requires:         %{name}%1 = %{epoch}:%{version}-%{release}
# Post requires alternatives to install tool alternatives.
Requires(post):   %{_sbindir}/alternatives
# Postun requires alternatives to uninstall tool alternatives.
Requires(postun): %{_sbindir}/alternatives

# Standard JPackage devel provides.
#Provides: java-sdk-%{javaver}-%{origin}%1 = %{epoch}:%{version}
#Provides: java-sdk-%{javaver}%1 = %{epoch}:%{version}
#Provides: java-sdk-%{origin}%1 = %{epoch}:%{version}
#Provides: java-sdk%1 = %{epoch}:%{javaver}
#Provides: java-%{javaver}-devel%1 = %{epoch}:%{version}
#Provides: java-devel-%{origin}%1 = %{epoch}:%{version}
#Provides: java-devel%1 = %{epoch}:%{javaver}

#Obsoletes: java-1.7.0-openjdk-devel%1
#Obsoletes: java-1.5.0-gcj-devel%1
}


%global java_demo_rpo() %{expand:
Requires: %{name}%1 = %{epoch}:%{version}-%{release}

#Obsoletes: java-1.7.0-openjdk-demo%1
}

%global java_javadoc_rpo() %{expand:
# Post requires alternatives to install javadoc alternative.
Requires(post):   %{_sbindir}/alternatives
# Postun requires alternatives to uninstall javadoc alternative.
Requires(postun): %{_sbindir}/alternatives

# Standard JPackage javadoc provides.
Provides: java-javadoc%1 = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-javadoc%1 = %{epoch}:%{version}-%{release}

#Obsoletes: java-1.7.0-openjdk-javadoc%1

}

%global java_src_rpo() %{expand:
Requires: %{name}-headless%1 = %{epoch}:%{version}-%{release}

#Obsoletes: java-1.7.0-openjdk-src%1
}

# Prevent brp-java-repack-jars from being run.
%global __jar_repack 0

Name:    java-%{javaver}-%{origin}
Version: %{javaver}.%{updatever}.%{buildver}
Release: 0%{?dist}
# java-1.5.0-ibm from jpackage.org set Epoch to 1 for unknown reasons
# and this change was brought into RHEL-4. java-1.5.0-ibm packages
# also included the epoch in their virtual provides. This created a
# situation where in-the-wild java-1.5.0-ibm packages provided "java =
# 1:1.5.0".  In RPM terms, "1.6.0 < 1:1.5.0" since 1.6.0 is
# interpreted as 0:1.6.0.  So the "java >= 1.6.0" requirement would be
# satisfied by the 1:1.5.0 packages.  Thus we need to set the epoch in
# JDK package >= 1.6.0 to 1, and packages referring to JDK virtual
# provides >= 1.6.0 must specify the epoch, "java >= 1:1.6.0".

Epoch:   1
Summary: OpenJDK Runtime Environment
Group:   Development/Languages

# HotSpot code is licensed under GPLv2
# JDK library code is licensed under GPLv2 with the Classpath exception
# The Apache license is used in code taken from Apache projects (primarily JAXP & JAXWS)
# DOM levels 2 & 3 and the XML digital signature schemas are licensed under the W3C Software License
# The JSR166 concurrency code is in the public domain
# The BSD and MIT licenses are used for a number of third-party libraries (see THIRD_PARTY_README)
# The OpenJDK source tree includes the JPEG library (IJG), zlib & libpng (zlib), giflib and LCMS (MIT)
# The test code includes copies of NSS under the Mozilla Public License v2.0
# The PCSClite headers are under a BSD with advertising license
# The elliptic curve cryptography (ECC) source code is licensed under the LGPLv2.1 or any later version
License:  ASL 1.1 and ASL 2.0 and BSD and BSD with advertising and GPL+ and GPLv2 and GPLv2 with exceptions and IJG and LGPLv2+ and MIT and MPLv2.0 and Public Domain and W3C and zlib
URL:      http://openjdk.java.net/

# Shenandoah HotSpot
# aarch64-port/jdk8u-shenandoah contains an integration forest of
# OpenJDK 8u, the aarch64 port and Shenandoah
# To regenerate, use:
# VERSION=%%{shenandoah_revision}
# FILE_NAME_ROOT=%%{shenandoah_project}-%%{shenandoah_repo}-${VERSION}
# REPO_ROOT=<path to checked-out repository> generate_source_tarball.sh
# where the source is obtained from http://hg.openjdk.java.net/%%{project}/%%{repo}
Source0: %{shenandoah_project}-%{shenandoah_repo}-%{shenandoah_revision}.tar.xz

# Custom README for -src subpackage
Source2:  README.src

# Use 'generate_tarballs.sh' to generate the following tarballs
# They are based on code contained in the IcedTea project (3.x).

# Systemtap tapsets. Zipped up to keep it small.
Source8: systemtap-tapset-3.6.0pre02.tar.xz

# Desktop files. Adapated from IcedTea.
Source9: jconsole.desktop.in
Source10: policytool.desktop.in

# nss configuration file
Source11: nss.cfg

# Removed libraries that we link instead
Source12: %{name}-remove-intree-libraries.sh

# Ensure we aren't using the limited crypto policy
Source13: TestCryptoLevel.java

# Missing headers not provided by nss-softokn
Source15: lowkeyti.h
Source16: softoknt.h

# Ensure ECDSA is working
Source17: TestECDSA.java

Source20: repackReproduciblePolycies.sh

# New versions of config files with aarch64 support. This is not upstream yet.
Source100: config.guess
Source101: config.sub

#############################################
#
# RPM/distribution specific patches
#
# This section includes patches specific to
# Fedora/RHEL which can not be upstreamed
# either in their current form or at all.
############################################

# Accessibility patches
# Ignore AWTError when assistive technologies are loaded 
Patch1:   rh1648242-accessible_toolkit_crash_do_not_break_jvm.patch
# PR1834, RH1022017: Reduce curves reported by SSL to those in NSS
# Not currently suitable to go upstream as it disables curves
# for all providers unconditionally
Patch525: pr1834-rh1022017-reduce_ellipticcurvesextension_to_provide_only_three_nss_supported_nist_curves_23_24_25.patch
# Turn on AssumeMP by default on RHEL systems
Patch534: rh1648246-always_instruct_vm_to_assume_multiple_processors_are_available.patch
# Reduce autoconf version requirement to allow use on RHEL 6
Patch998: rh1649731-allow_to_build_on_rhel6_with_stdcpplib_autotools_2_63.patch

#############################################
#
# Upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed to the current development
# tree of OpenJDK.
#############################################
# PR2737: Allow multiple initialization of PKCS11 libraries
Patch5: pr2737-allow_multiple_pkcs11_library_initialisation_to_be_a_non_critical_error.patch
# PR2095, RH1163501: 2048-bit DH upper bound too small for Fedora infrastructure (sync with IcedTea 2.x)
Patch504: rh1163501-increase_2048_bit_dh_upper_bound_fedora_infrastructure_in_dhparametergenerator.patch
# S4890063, PR2304, RH1214835: HPROF: default text truncated when using doe=n option
Patch511: jdk4890063-pr2304-rh1214835-jvmti_hprof_default_text_truncated_when_using_doe_equals_n_option.patch
# Turn off strict overflow on IndicRearrangementProcessor{,2}.cpp following 8140543: Arrange font actions
Patch512: rh1649664-awt2dlibraries_compiled_with_no_strict_overflow.patch
# Support for building the SunEC provider with the system NSS installation
# PR1983: Support using the system installation of NSS with the SunEC provider
# PR2127: SunEC provider crashes when built using system NSS
# PR2815: Race condition in SunEC provider with system NSS
# PR2899: Don't use WithSeed versions of NSS functions as they don't fully process the seed
# PR2934: SunEC provider throwing KeyException with current NSS
# PR3479, RH1486025: ECC and NSS JVM crash
Patch513: pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_jdk8.patch
Patch514: pr1983-rh1565658-support_using_the_system_installation_of_nss_with_the_sunec_provider_root8.patch
Patch515: pr2127-sunec_provider_crashes_when_built_using_system_nss_thus_use_of_nss_memory_management_functions.patch
Patch516: pr2815-race_condition_in_sunec_provider_with_system_nss_fix.patch
Patch517: pr2899-dont_use_withseed_versions_of_nss_functions_as_they_dont_fully_process_the_seed.patch
Patch518: pr2934-sunec_provider_throwing_keyexception_withine.separator_current_nss_thus_initialise_the_random_number_generator_and_feed_the_seed_to_it.patch
Patch519: pr3479-rh1486025-sunec_provider_can_have_multiple_instances_leading_to_premature_nss_shutdown.patch
# RH1566890: CVE-2018-3639
Patch529: rh1566890-CVE_2018_3639-speculative_store_bypass.patch
Patch531: rh1566890-CVE_2018_3639-speculative_store_bypass_toggle.patch
# JDK-8009550, RH910107: PlatformPCSC should load versioned so
Patch541: rh1684077-openjdk_should_depend_on_pcsc-lite-libs_instead_of_pcsc-lite-devel.patch

#############################################
#
# Arch-specific upstreamable patches
#
# This section includes patches which need to
# be reviewed & pushed upstream and are specific
# to certain architectures. This usually means the
# current OpenJDK development branch, but may also
# include other trees e.g. for the AArch64 port for
# OpenJDK 8u.
#############################################
# s390: Type fixing for s390
Patch102: jdk8203030-zero_s390_31_bit_size_t_type_conflicts_in_shared_code.patch
# s390: PR3593: Use "%z" for size_t on s390 as size_t != intptr_t
Patch103: pr3593-s390_use_z_format_specifier_for_size_t_arguments_as_size_t_not_equals_to_int.patch
# x86: S8199936, PR3533: HotSpot generates code with unaligned stack, crashes on SSE operations (-mstackrealign workaround)
Patch105: jdk8199936-pr3533-enable_mstackrealign_on_x86_linux_as_well_as_x86_mac_os_x.patch
# S390 ambiguous log2_intptr calls
Patch107: s390-8214206_fix.patch

#############################################
#
# Patches which need backporting to 8u
#
# This section includes patches which have
# been pushed upstream to the latest OpenJDK
# development tree, but need to be backported
# to OpenJDK 8u.
#############################################
# 8035341: Allow using a system installed libpng
Patch202: jdk8035341-allow_using_system_installed_libpng.patch
# 8042159: Allow using a system-installed lcms2
Patch203: jdk8042159-allow_using_system_installed_lcms2.patch
# PR2462: Backport "8074839: Resolve disabled warnings for libunpack and the unpack200 binary"
# S8074839, PR2462: Resolve disabled warnings for libunpack and the unpack200 binary
# This fixes printf warnings that lead to build failure with -Werror=format-security from optflags
Patch502: pr2462-resolve_disabled_warnings_for_libunpack_and_the_unpack200_binary.patch
# 8171000, PR3542, RH1402819: Robot.createScreenCapture() crashes in wayland mode
Patch563: jdk8171000-pr3542-rh1402819-robot_createScreenCapture_crashes_in_wayland_mode.patch
# 8197546, PR3542, RH1402819: Fix for 8171000 breaks Solaris + Linux builds
Patch564: jdk8197546-pr3542-rh1402819-fix_for_8171000_breaks_solaris_linux_builds.patch
# PR3591: Fix for bug 3533 doesn't add -mstackrealign to JDK code
Patch571: jdk8199936-pr3591-enable_mstackrealign_on_x86_linux_as_well_as_x86_mac_os_x_jdk.patch

#############################################
#
# Patches appearing in 8u222
#
# This section includes patches which are present
# in the listed OpenJDK 8u release and should be
# able to be removed once that release is out
# and used by this RPM.
#############################################

#############################################
#
# Patches ineligible for 8u
#
# This section includes patches which are present
# upstream, but ineligible for upstream 8u backport.
#############################################
# 8043805: Allow using a system-installed libjpeg
Patch201: jdk8043805-allow_using_system_installed_libjpeg.patch

#############################################
#
# Shenandoah fixes
#
# This section includes patches which are
# specific to the Shenandoah garbage collector
# and should be upstreamed to the appropriate
# trees.
#############################################

# Shenandoah fixes
# PR3634: Shenandoah still broken on s390 with aarch64-shenandoah-jdk8u181-b16
Patch582: pr3634-fix_shenandoah_for_size_t_on_s390.patch

#############################################
#
# Non-OpenJDK fixes
#
# This section includes patches to code other
# that from OpenJDK.
#############################################

# Section currently empty

#############################################
#
# Dependencies
#
#############################################
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: alsa-lib-devel
BuildRequires: binutils
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
BuildRequires: fontconfig
BuildRequires: freetype-devel
BuildRequires: giflib-devel
BuildRequires: gcc-c++
BuildRequires: gtk2-devel
#BuildRequires: lcms2-devel # no lcms2 in rhel 6
BuildRequires: libjpeg-devel
BuildRequires: libpng-devel
BuildRequires: libxslt
BuildRequires: libX11-devel
BuildRequires: libXi-devel
BuildRequires: libXinerama-devel
BuildRequires: libXt-devel
BuildRequires: libXtst-devel
# Requirements for setting up the nss.cfg
BuildRequires: nss-devel
BuildRequires: pkgconfig
BuildRequires: xorg-x11-proto-devel
BuildRequires: zip
# Use OpenJDK 7 where available (on RHEL) to avoid
# having to use the rhel-6.x-java-unsafe-candidate hack
%if 0%{?rhel}
BuildRequires: java-1.7.0-openjdk-devel
%else
BuildRequires: java-1.8.0-openjdk-devel
%endif
# Zero-assembler build requirement.
%ifnarch %{jit_arches}
BuildRequires: libffi-devel
%endif
BuildRequires: tzdata-java >= 2015d
# Build requirements for SunEC system NSS support
BuildRequires: nss-softokn-freebl-devel >= 3.14.3-18

# cacerts build requirement.
BuildRequires: openssl
%if %{with_systemtap}
BuildRequires: systemtap-sdt-devel
%endif


# this is built always, also during debug-only build
# when it is built in debug-only, then this package is just placeholder
%{java_rpo %{nil}}

%description
The OpenJDK runtime environment.

%if %{include_debug_build}
%package debug
Summary: OpenJDK Runtime Environment %{debug_on}
Group:   Development/Languages

%{java_rpo -- %{debug_suffix_unquoted}}
%description debug
The OpenJDK runtime environment.
%{debug_warning}
%endif

%if %{include_normal_build}
%package headless
Summary: OpenJDK Runtime Environment
Group:   Development/Languages

%{java_headless_rpo %{nil}}

%description headless
The OpenJDK runtime environment without audio and video support.
%endif

%if %{include_debug_build}
%package headless-debug
Summary: OpenJDK Runtime Environment %{debug_on}
Group:   Development/Languages

%{java_headless_rpo -- %{debug_suffix_unquoted}}

%description headless-debug
The OpenJDK runtime environment without audio and video support.
%{debug_warning}
%endif

%if %{include_normal_build}
%package devel
Summary: OpenJDK Development Environment
Group:   Development/Tools

%{java_devel_rpo %{nil}}

%description devel
The OpenJDK development tools.
%endif

%if %{include_debug_build}
%package devel-debug
Summary: OpenJDK Development Environment %{debug_on}
Group:   Development/Tools

%{java_devel_rpo -- %{debug_suffix_unquoted}}

%description devel-debug
The OpenJDK development tools.
%{debug_warning}
%endif

%if %{include_normal_build}
%package demo
Summary: OpenJDK Demos
Group:   Development/Languages

%{java_demo_rpo %{nil}}

%description demo
The OpenJDK demos.
%endif

%if %{include_debug_build}
%package demo-debug
Summary: OpenJDK Demos %{debug_on}
Group:   Development/Languages

%{java_demo_rpo -- %{debug_suffix_unquoted}}

%description demo-debug
The OpenJDK demos.
%{debug_warning}
%endif

%if %{include_normal_build}
%package src
Summary: OpenJDK Source Bundle
Group:   Development/Languages

%{java_src_rpo %{nil}}

%description src
The OpenJDK source bundle.
%endif

%if %{include_debug_build}
%package src-debug
Summary: OpenJDK Source Bundle %{for_debug}
Group:   Development/Languages

%{java_src_rpo -- %{debug_suffix_unquoted}}

%description src-debug
The OpenJDK source bundle %{for_debug}.
%endif

%if %{include_normal_build}
%package javadoc
Summary: OpenJDK API Documentation
Group:   Documentation
Requires: jpackage-utils
BuildArch: noarch

%{java_javadoc_rpo %{nil}}

%description javadoc
The OpenJDK API documentation.
%endif

%if %{include_debug_build}
%package javadoc-debug
Summary: OpenJDK API Documentation %{for_debug}
Group:   Documentation
Requires: jpackage-utils
BuildArch: noarch

%{java_javadoc_rpo -- %{debug_suffix_unquoted}}

%description javadoc-debug
The OpenJDK API documentation %{for_debug}.
%endif



%prep
if [ %{include_normal_build} -eq 0 -o  %{include_normal_build} -eq 1 ] ; then
  echo "include_normal_build is %{include_normal_build}"
else
  echo "include_normal_build is %{include_normal_build}, thats invalid. Use 1 for yes or 0 for no"
  exit 11
fi
if [ %{include_debug_build} -eq 0 -o  %{include_debug_build} -eq 1 ] ; then
  echo "include_debug_build is %{include_debug_build}"
else
  echo "include_debug_build is %{include_debug_build}, thats invalid. Use 1 for yes or 0 for no"
  exit 12
fi
if [ %{include_debug_build} -eq 0 -a  %{include_normal_build} -eq 0 ] ; then
  echo "you have disabled both include_debug_build and include_debug_build. no go."
  exit 13
fi
%setup -q -c -n %{uniquesuffix ""} -T -a 0
# https://bugzilla.redhat.com/show_bug.cgi?id=1189084
prioritylength=`expr length %{priority}`
if [ $prioritylength -ne 7 ] ; then
 echo "priority must be 7 digits in total, violated"
 exit 14
fi
# For old patches
ln -s %{top_level_dir_name} jdk8

cp %{SOURCE2} .

# Add local copies of missing NSS headers
cp -v %{SOURCE15} %{SOURCE16} openjdk/jdk/src/share/native/sun/security/ec

# replace outdated configure guess script
#
# the configure macro will do this too, but it also passes a few flags not
# supported by openjdk configure script
cp %{SOURCE100} %{top_level_dir_name}/common/autoconf/build-aux/
cp %{SOURCE101} %{top_level_dir_name}/common/autoconf/build-aux/

# OpenJDK patches

# Remove libraries that are linked
sh %{SOURCE12}

# System library fixes
%patch201
%patch202
%patch203

%patch1
%patch5

# s390 build fixes
%patch102
%patch103
%patch107

# x86 fixes
%patch105

# RHEL 6 fix
%patch998

# Upstreamable fixes
%patch502
%patch504
%patch511
%patch512
%patch513
%patch514
%patch515
%patch516
%patch517
%patch518
%patch519
%patch529
%patch531
%patch563
%patch564
%patch571
%patch541

# RPM-only fixes
%patch525

# RHEL-only patches
%if 0%{?rhel}
%patch534
%endif

# Shenandoah patches
%patch582

# Extract systemtap tapsets
%if %{with_systemtap}
tar -x -I xz -f %{SOURCE8}
%if %{include_debug_build}
cp -r tapset tapset%{debug_suffix}
%endif


for suffix in %{build_loop} ; do
  for file in "tapset"$suffix/*.in; do
    OUTPUT_FILE=`echo $file | sed -e s:%{javaver}\.stp\.in$:%{version}-%{release}.%{_arch}.stp:g`
    sed -e s:@ABS_SERVER_LIBJVM_SO@:%{_jvmdir}/%{sdkdir $suffix}/jre/lib/%{archinstall}/server/libjvm.so:g $file > $file.1
# TODO find out which architectures other than i686 have a client vm
%ifarch %{ix86}
    sed -e s:@ABS_CLIENT_LIBJVM_SO@:%{_jvmdir}/%{sdkdir $suffix}/jre/lib/%{archinstall}/client/libjvm.so:g $file.1 > $OUTPUT_FILE
%else
    sed -e '/@ABS_CLIENT_LIBJVM_SO@/d' $file.1 > $OUTPUT_FILE
%endif
    sed -i -e s:@ABS_JAVA_HOME_DIR@:%{_jvmdir}/%{sdkdir $suffix}:g $OUTPUT_FILE
    sed -i -e s:@INSTALL_ARCH_DIR@:%{archinstall}:g $OUTPUT_FILE
    sed -i -e s:@prefix@:%{_jvmdir}/%{sdkdir $suffix}/:g $OUTPUT_FILE
  done
done
# systemtap tapsets ends
%endif

# Prepare desktop files
for suffix in %{build_loop} ; do
for file in %{SOURCE9} %{SOURCE10} ; do
    FILE=`basename $file | sed -e s:\.in$::g`
    EXT="${FILE##*.}"
    NAME="${FILE%.*}"
    OUTPUT_FILE=$NAME$suffix.$EXT
    sed -e s:#JAVA_HOME#:%{sdkbindir $suffix}:g $file > $OUTPUT_FILE
    sed -i -e  s:#JRE_HOME#:%{jrebindir $suffix}:g $OUTPUT_FILE
    sed -i -e  s:#ARCH#:%{version}-%{release}.%{_arch}$suffix:g $OUTPUT_FILE
done
done

%build
# How many cpu's do we have?
export NUM_PROC=%(/usr/bin/getconf _NPROCESSORS_ONLN 2> /dev/null || :)
export NUM_PROC=${NUM_PROC:-1}
%if 0%{?_smp_ncpus_max}
# Honor %%_smp_ncpus_max
[ ${NUM_PROC} -gt %{?_smp_ncpus_max} ] && export NUM_PROC=%{?_smp_ncpus_max}
%endif

# Build IcedTea and OpenJDK.
%ifarch s390x sparc64 alpha %{power64} %{aarch64}
export ARCH_DATA_MODEL=64
%endif
%ifarch alpha
export CFLAGS="$CFLAGS -mieee"
%endif

# We use ourcppflags because the OpenJDK build seems to
# pass these to the HotSpot C++ compiler...
EXTRA_CFLAGS="%ourcppflags"
# Disable various optimizations to fix miscompliation. See:
# - https://bugzilla.redhat.com/show_bug.cgi?id=1120792
EXTRA_CPP_FLAGS="%ourcppflags -fno-tree-vrp"
# PPC/PPC64 needs -fno-tree-vectorize since -O3 would
# otherwise generate wrong code producing segfaults.
%ifarch %{power64} ppc
EXTRA_CFLAGS="$EXTRA_CFLAGS -fno-tree-vectorize"
# fix rpmlint warnings
EXTRA_CFLAGS="$EXTRA_CFLAGS -fno-strict-aliasing"
%endif
export EXTRA_CFLAGS

(cd %{top_level_dir_name}/common/autoconf
 bash ./autogen.sh
)

for suffix in %{build_loop} ; do
if [ "$suffix" = "%{debug_suffix}" ] ; then
debugbuild=%{debugbuild_parameter}
else
debugbuild=%{normalbuild_parameter}
fi

# Variable used in hs_err hook on build failures
top_dir_abs_path=$(pwd)/%{top_level_dir_name}

mkdir -p %{buildoutputdir $suffix}
pushd %{buildoutputdir $suffix}

NSS_LIBS="%{NSS_LIBS} -lfreebl -lsoftokn" \
NSS_CFLAGS="%{NSS_CFLAGS} -DLEGACY_NSS" \
bash ../../configure \
%ifnarch %{jit_arches}
    --with-jvm-variants=zero \
%endif
    --disable-zip-debug-info \
    --with-milestone="fcs" \
    --with-update-version=%{updatever} \
    --with-build-number=%{buildver} \
    --with-boot-jdk=/usr/lib/jvm/java-openjdk \
    --with-debug-level=$debugbuild \
    --enable-unlimited-crypto \
    --enable-system-nss \
    --with-zlib=system \
    --with-libjpeg=system \
    --with-giflib=system \
    --with-libpng=system \
    --with-lcms=bundled \
    --with-stdcpplib=dynamic \
    --with-extra-cxxflags="$EXTRA_CPP_FLAGS" \
    --with-extra-cflags="$EXTRA_CFLAGS" \
    --with-extra-ldflags="%{ourldflags}" \
    --with-num-cores="$NUM_PROC"

cat spec.gmk
cat hotspot-spec.gmk

# The combination of FULL_DEBUG_SYMBOLS=0 and ALT_OBJCOPY=/does_not_exist
# disables FDS for all build configs and reverts to pre-FDS make logic.
# STRIP_POLICY=none says don't do any stripping. DEBUG_BINARIES=true says
# ignore all the other logic about which debug options and just do '-g'.

make \
    DEBUG_BINARIES=true \
    JAVAC_FLAGS=-g \
    STRIP_POLICY=no_strip \
    POST_STRIP_CMD="" \
    LOG=trace \
    %{targets} || ( pwd; find $top_dir_abs_path -name "hs_err_pid*.log" | xargs cat && false )

# the build (erroneously) removes read permissions from some jars
# this is a regression in OpenJDK 7 (our compiler):
# http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=1437
find images/%{j2sdkimage} -iname '*.jar' -exec chmod ugo+r {} \;
chmod ugo+r images/%{j2sdkimage}/lib/ct.sym

# remove redundant *diz and *debuginfo files
find images/%{j2sdkimage} -iname '*.diz' -exec rm {} \;
find images/%{j2sdkimage} -iname '*.debuginfo' -exec rm {} \;

popd >& /dev/null

# Install nss.cfg right away as we will be using the JRE above
export JAVA_HOME=$(pwd)/%{buildoutputdir $suffix}/images/%{j2sdkimage}

# Install nss.cfg right away as we will be using the JRE above
install -m 644 %{SOURCE11} $JAVA_HOME/jre/lib/security/

# Use system-wide tzdata
rm $JAVA_HOME/jre/lib/tzdb.dat
ln -s %{_datadir}/javazi-1.8/tzdb.dat $JAVA_HOME/jre/lib/tzdb.dat

#build cycles
done

%check

# We test debug first as it will give better diagnostics on a crash
for suffix in %{rev_build_loop} ; do

export JAVA_HOME=$(pwd)/%{buildoutputdir $suffix}/images/%{j2sdkimage}

# Check unlimited policy has been used
$JAVA_HOME/bin/javac -d . %{SOURCE13}
$JAVA_HOME/bin/java TestCryptoLevel

# Check ECC is working
$JAVA_HOME/bin/javac -d . %{SOURCE17}
$JAVA_HOME/bin/java $(echo $(basename %{SOURCE17})|sed "s|\.java||")

# Check debug symbols are present and can identify code
SERVER_JVM="$JAVA_HOME/jre/lib/%{archinstall}/server/libjvm.so"
if [ -f "$SERVER_JVM" ] ; then
  nm -aCl "$SERVER_JVM" | grep javaCalls.cpp
fi
CLIENT_JVM="$JAVA_HOME/jre/lib/%{archinstall}/client/libjvm.so"
if [ -f "$CLIENT_JVM" ] ; then
  nm -aCl "$CLIENT_JVM" | grep javaCalls.cpp
fi
ZERO_JVM="$JAVA_HOME/jre/lib/%{archinstall}/zero/libjvm.so"
if [ -f "$ZERO_JVM" ] ; then
  nm -aCl "$ZERO_JVM" | grep javaCalls.cpp
fi

# Check src.zip has all sources. See RHBZ#1130490
jar -tf $JAVA_HOME/src.zip | grep 'sun.misc.Unsafe'

# Check class files include useful debugging information
$JAVA_HOME/bin/javap -l java.lang.Object | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.lang.Object | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.lang.Object | grep LocalVariableTable

# Check generated class files include useful debugging information
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LocalVariableTable

#build cycles
done

%install
rm -rf $RPM_BUILD_ROOT
STRIP_KEEP_SYMTAB=libjvm*

for suffix in %{build_loop} ; do

pushd %{buildoutputdir  $suffix}/images/%{j2sdkimage}

#install jsa directories so we can owe them
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix}/lib/%{archinstall}/server/
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix}/lib/%{archinstall}/client/

  # Install main files.
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}
  cp -a bin include lib src.zip $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix}
  cp -a jre/bin jre/lib $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix}

%if %{with_systemtap}
  # Install systemtap support files.
  install -dm 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/tapset
  # note, that uniquesuffix  is in BUILD dir in this case
  cp -a $RPM_BUILD_DIR/%{uniquesuffix ""}/tapset$suffix/*.stp $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/tapset/
  pushd  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/tapset/
   tapsetFiles=`ls *.stp`
  popd
  install -d -m 755 $RPM_BUILD_ROOT%{tapsetdir}
  pushd $RPM_BUILD_ROOT%{tapsetdir}
    RELATIVE=$(%{abs2rel} %{_jvmdir}/%{sdkdir $suffix}/tapset %{tapsetdir})
    for name in $tapsetFiles ; do
      targetName=`echo $name | sed "s/.stp/$suffix.stp/"`
      ln -sf $RELATIVE/$name $targetName
    done
  popd
%endif

  # Install cacerts symlink.
  rm -f $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix}/lib/security/cacerts
  pushd $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix}/lib/security
    RELATIVE=$(%{abs2rel} %{_sysconfdir}/pki/java \
      %{_jvmdir}/%{jredir $suffix}/lib/security)
    ln -sf $RELATIVE/cacerts .
  popd

  # Install extension symlinks.
  install -d -m 755 $RPM_BUILD_ROOT%{jvmjardir $suffix}
  pushd $RPM_BUILD_ROOT%{jvmjardir $suffix}
    RELATIVE=$(%{abs2rel} %{_jvmdir}/%{jredir $suffix}/lib %{jvmjardir $suffix})
    ln -sf $RELATIVE/jsse.jar jsse-%{version}.jar
    ln -sf $RELATIVE/jce.jar jce-%{version}.jar
    ln -sf $RELATIVE/rt.jar jndi-%{version}.jar
    ln -sf $RELATIVE/rt.jar jndi-ldap-%{version}.jar
    ln -sf $RELATIVE/rt.jar jndi-cos-%{version}.jar
    ln -sf $RELATIVE/rt.jar jndi-rmi-%{version}.jar
    ln -sf $RELATIVE/rt.jar jaas-%{version}.jar
    ln -sf $RELATIVE/rt.jar jdbc-stdext-%{version}.jar
    ln -sf jdbc-stdext-%{version}.jar jdbc-stdext-3.0.jar
    ln -sf $RELATIVE/rt.jar sasl-%{version}.jar
    for jar in *-%{version}.jar
    do
      if [ x%{version} != x%{javaver} ]
      then
        ln -sf $jar $(echo $jar | sed "s|-%{version}.jar|-%{javaver}.jar|g")
      fi
      ln -sf $jar $(echo $jar | sed "s|-%{version}.jar|.jar|g")
    done
  popd

  # Install JCE policy symlinks.
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmprivdir}/%{uniquesuffix $suffix}/jce/vanilla

  # Install versioned symlinks.
  pushd $RPM_BUILD_ROOT%{_jvmdir}
    ln -sf %{jredir $suffix} %{jrelnk $suffix}
  popd

  pushd $RPM_BUILD_ROOT%{_jvmjardir}
    ln -sf %{sdkdir $suffix} %{jrelnk $suffix}
  popd

  # Remove javaws man page
  rm -f man/man1/javaws*

  # Install man pages.
  install -d -m 755 $RPM_BUILD_ROOT%{_mandir}/man1
  for manpage in man/man1/*
  do
    # Convert man pages to UTF8 encoding.
    iconv -f ISO_8859-1 -t UTF8 $manpage -o $manpage.tmp
    mv -f $manpage.tmp $manpage
    install -m 644 -p $manpage $RPM_BUILD_ROOT%{_mandir}/man1/$(basename \
      $manpage .1)-%{uniquesuffix $suffix}.1
  done

  # Install demos and samples.
  cp -a demo $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}
  mkdir -p sample/rmi
  if [ ! -e sample/rmi/java-rmi.cgi ] ; then 
    # hack to allow --short-circuit on install
    mv bin/java-rmi.cgi sample/rmi
  fi
  cp -a sample $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}

popd


# Install Javadoc documentation.
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}
cp -a %{buildoutputdir $suffix}/docs $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir $suffix}

# Install icons and menu entries.
for s in 16 24 32 48 ; do
  install -D -p -m 644 \
    %{top_level_dir_name}/jdk/src/solaris/classes/sun/awt/X11/java-icon${s}.png \
    $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${s}x${s}/apps/java-%{javaver}.png
done

# Install desktop files.
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/{applications,pixmaps}
for e in jconsole$suffix policytool$suffix ; do
    desktop-file-install --vendor=%{uniquesuffix $suffix} --mode=644 \
        --dir=$RPM_BUILD_ROOT%{_datadir}/applications $e.desktop
done

# Install /etc/.java/.systemPrefs/ directory
# See https://bugzilla.redhat.com/show_bug.cgi?id=741821
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/.java/.systemPrefs

# Find JRE directories.
find $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix} -type d \
  | grep -v jre/lib/security \
  | sed 's|'$RPM_BUILD_ROOT'|%dir |' \
  > %{name}.files-headless"$suffix"
# Find JRE files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{jredir $suffix} -type f -o -type l \
  | grep -v jre/lib/security \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  > %{name}.files.all"$suffix"
#split %%{name}.files to %%{name}.files-headless and %%{name}.files
#see https://bugzilla.redhat.com/show_bug.cgi?id=875408
NOT_HEADLESS=\
"%{_jvmdir}/%{uniquesuffix $suffix}/jre/lib/%{archinstall}/libjsoundalsa.so
%{_jvmdir}/%{uniquesuffix $suffix}/jre/lib/%{archinstall}/libpulse-java.so
%{_jvmdir}/%{uniquesuffix $suffix}/jre/lib/%{archinstall}/libsplashscreen.so
%{_jvmdir}/%{uniquesuffix $suffix}/jre/lib/%{archinstall}/libawt_xawt.so
%{_jvmdir}/%{uniquesuffix $suffix}/jre/lib/%{archinstall}/libjawt.so
%{_jvmdir}/%{uniquesuffix $suffix}/jre/bin/policytool"
#filter  %%{name}.files from  %%{name}.files.all to %%{name}.files-headless
ALL=`cat %{name}.files.all"$suffix"`
for file in $ALL ; do 
  INLCUDE="NO" ; 
  for blacklist in $NOT_HEADLESS ; do
#we can not match normally, because rpmbuild will evaluate !0 result as script failure
    q=`expr match "$file" "$blacklist"` || :
    l=`expr length  "$blacklist"` || :
    if [ $q -eq $l  ]; then 
      INLCUDE="YES" ; 
    fi;
done
if [ "x$INLCUDE" = "xNO"  ]; then 
    echo "$file" >> %{name}.files-headless"$suffix"
else
    echo "$file" >> %{name}.files"$suffix"
fi
done
# Find demo directories.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/sample -type d \
  | sed 's|'$RPM_BUILD_ROOT'|%dir |' \
  > %{name}-demo.files"$suffix"

# FIXME: remove SONAME entries from demo DSOs.  See
# https://bugzilla.redhat.com/show_bug.cgi?id=436497

# Find non-documentation demo files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/sample \
  -type f -o -type l | sort \
  | grep -v README \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  >> %{name}-demo.files"$suffix"
# Find documentation demo files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir $suffix}/sample \
  -type f -o -type l | sort \
  | grep README \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  | sed 's|^|%doc |' \
  >> %{name}-demo.files"$suffix"

bash %{SOURCE20} $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir $suffix} %{javaver}

#rhel 6 only fix for https://bugzilla.redhat.com/show_bug.cgi?id=1217177
ln -sf %{sdkdir $suffix}  $RPM_BUILD_ROOT/%{sdk_versionless_lnk $suffix}
ln -sf %{sdkdir $suffix}/jre  $RPM_BUILD_ROOT/%{jre_versionless_lnk $suffix}
ln -sf %{_jvmjardir}/%{sdkdir  $suffix}  $RPM_BUILD_ROOT/%{_jvmjardir}/java-%{javaver}-%{origin}.%{_arch}"$suffix"
ln -sf %{_jvmjardir}/%{sdkdir  $suffix}  $RPM_BUILD_ROOT/%{_jvmjardir}/jre-%{javaver}-%{origin}.%{_arch}"$suffix"
#end of fix of rhbz#1217177

# end, dual install
done

%if %{include_normal_build} 
# intentioanlly only for non-debug
%pretrans headless -p <lua>
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1290388 for pretrans over pre
-- if copy-jdk-configs is in transaction, it installs in pretrans to temp
-- if copy_jdk_configs is in temp, then it means that copy-jdk-configs is in tranasction  and so is
-- preferred over one in %%{_libexecdir}. If it is not in transaction, then depends 
-- whether copy-jdk-configs is installed or not. If so, then configs are copied
-- (copy_jdk_configs from %%{_libexecdir} used) or not copied at all
local posix = require "posix"
local debug = false

SOURCE1 = "%{rpm_state_dir}/copy_jdk_configs.lua"
SOURCE2 = "%{_libexecdir}/copy_jdk_configs.lua"

local stat1 = posix.stat(SOURCE1, "type");
local stat2 = posix.stat(SOURCE2, "type");

  if (stat1 ~= nil) then
  if (debug) then
    print(SOURCE1 .." exists - copy-jdk-configs in transaction, using this one.")
  end;
  package.path = package.path .. ";" .. SOURCE1
else 
  if (stat2 ~= nil) then
  if (debug) then
    print(SOURCE2 .." exists - copy-jdk-configs alrady installed and NOT in transation. Using.")
  end;
  package.path = package.path .. ";" .. SOURCE2
  else
    if (debug) then
      print(SOURCE1 .." does NOT exists")
      print(SOURCE2 .." does NOT exists")
      print("No config files will be copied")
    end
  return
  end
end
-- run contetn of included file with fake args
arg = {"--currentjvm", "%{uniquesuffix %{nil}}", "--jvmdir", "%{_jvmdir %{nil}}", "--origname", "%{name}", "--origjavaver", "%{javaver}", "--arch", "%{_arch}", "--temp", "%{rpm_state_dir}/%{name}.%{_arch}"}
require "copy_jdk_configs.lua"

%post 
%{post_script %{nil}}

%post headless
%{post_headless %{nil}}

%postun
%{postun_script %{nil}}

%postun headless
%{postun_headless %{nil}}

%posttrans
%{posttrans_script %{nil}}

%post devel
%{post_devel %{nil}}

%postun devel
%{postun_devel %{nil}}

%posttrans  devel
%{posttrans_devel %{nil}}

%post javadoc
%{post_javadoc %{nil}}

%postun javadoc
%{postun_javadoc %{nil}}
%endif

%if %{include_debug_build}
%post debug
%{post_script -- %{debug_suffix_unquoted}}

%post headless-debug
%{post_headless -- %{debug_suffix_unquoted}}

%postun debug
%{postun_script -- %{debug_suffix_unquoted}}

%postun headless-debug
%{postun_headless -- %{debug_suffix_unquoted}}

%posttrans debug
%{posttrans_script -- %{debug_suffix_unquoted}}

%post devel-debug
%{post_devel -- %{debug_suffix_unquoted}}

%postun devel-debug
%{postun_devel -- %{debug_suffix_unquoted}}

%posttrans  devel-debug
%{posttrans_devel -- %{debug_suffix_unquoted}}

%post javadoc-debug
%{post_javadoc -- %{debug_suffix_unquoted}}

%postun javadoc-debug
%{postun_javadoc -- %{debug_suffix_unquoted}}
%endif

%if %{include_normal_build}
%files -f %{name}.files
# main package builds always
%{files_jre %{nil}}
%else
%files
# placeholder
%endif


%if %{include_normal_build} 
%files headless  -f %{name}.files-headless
# important note, see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue 
# all config/norepalce files (and more) have to be declared in pretrans. See pretrans
%{files_jre_headless %{nil}}

%files devel
%{files_devel %{nil}}

%files demo -f %{name}-demo.files
%{files_demo %{nil}}

%files src
%{files_src %{nil}}

%files javadoc
%{files_javadoc %{nil}}
%endif

%if %{include_debug_build}
%files debug -f %{name}.files-debug
%{files_jre -- %{debug_suffix_unquoted}}

%files headless-debug  -f %{name}.files-headless-debug
%{files_jre_headless -- %{debug_suffix_unquoted}}

%files devel-debug
%{files_devel -- %{debug_suffix_unquoted}}

%files demo-debug -f %{name}-demo.files-debug
%{files_demo -- %{debug_suffix_unquoted}}

%files src-debug
%{files_src -- %{debug_suffix_unquoted}}

%files javadoc-debug
%{files_javadoc -- %{debug_suffix_unquoted}}
%endif

%changelog
* Thu Apr 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b04-1
- Update to aarch64-shenandoah-jdk8u212-b04.
- Resolves: rhbz#1693468

* Thu Apr 11 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b03-0
- Update to aarch64-shenandoah-jdk8u212-b03.
- Resolves: rhbz#1693468

* Tue Apr 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.212.b02-0
- Update to aarch64-shenandoah-jdk8u212-b02.
- Remove patches included upstream
  - JDK-8197429/PR3546/RH153662{2,3}
  - JDK-8184309/PR3596
- Re-generate patches
  - JDK-8203030
- Add casts to resolve s390 ambiguity in calls to log2_intptr
- Resolves: rhbz#1693468

* Sun Apr 07 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.202.b08-0
- Update to aarch64-shenandoah-jdk8u202-b08.
- Remove patches included upstream
  - JDK-8211387/PR3559
  - JDK-8073139/PR1758/RH1191652
  - JDK-8044235
  - JDK-8131048/PR3574/RH1498936
  - JDK-8164920/PR3574/RH1498936
- Resolves: rhbz#1693468

* Thu Apr 04 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b13-0
- Update to aarch64-shenandoah-jdk8u201-b13.
- Drop JDK-8160748 & JDK-8189170 AArch64 patches now applied upstream.
- Resolves: rhbz#1693468

* Tue Apr 02 2019 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.201.b09-3
- Update patch for RH1566890.
  - Renamed rh1566890_speculative_store_bypass_so_added_more_per_task_speculation_control_CVE_2018_3639 to
    rh1566890-CVE_2018_3639-speculative_store_bypass.patch
  - Added dependent patch,
    rh1566890-CVE_2018_3639-speculative_store_bypass_toggle.patch
- Resolves: rhbz#1693468

* Thu Feb 28 2019 Jiri Vanek jvanek@redhat.com - 1:1.8.0.201.b09-2
- Replaced pcsc-lite-devel (which is in optional channel) with pcsc-lite-libs.
- added rh1684077-openjdk_should_depend_on_pcsc-lite-libs_instead_of_pcsc-lite-devel.patch to make jdk work with pcsc

* Wed Jan 16 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.201.b09-0
- Update to aarch64-shenandoah-jdk8u201-b09.
- Resolves: rhbz#1661577

* Wed Jan 16 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.192.b12-1
- Add 8160748 for AArch64 which is missing from upstream 8u version.
- Add port of 8189170 to AArch64 which is missing from upstream 8u version.
- Resolves: rhbz#1661577

* Wed Jan 16 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.192.b12-0
- Update to aarch64-shenandoah-jdk8u192-b12.
- Remove patches included upstream
  - PR3548/RH1540242
  - JDK-6260348/PR3066
  - JDK-8185723/PR3553
  - JDK-8186461/PR3557
  - JDK-8201509/PR3579
  - JDK-8205104/PR3539/RH1548475
  - JDK-8206406/PR3610/RH1597825
  - JDK-8201495/PR2415
- Re-generate patches (mostly due to upstream build changes)
  - JDK-8073139/PR1758/RH1191652
  - JDK-8197429/PR3546/RH1536622 (due to JDK-8189170)
  - JDK-8199936/PR3533
  - JDK-8199936/PR3591
  - PR3559 (due to JDK-8185723/JDK-8186461/JDK-8201509)
  - PR3593 (due to JDK-8081202)
  - RH1566890/CVE-2018-3639 (due to JDK-8189170)
  - RH1649664 (due to JDK-8196516)
  - RH1649731
- Resolves: rhbz#1661577

* Mon Jan 14 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b14-1
- Add 8131048 & 8164920 (PR3574/RH1498936) to provide a CRC32 intrinsic for PPC64.
- Resolves: rhbz#1661577

* Thu Jan 10 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b14-0
- Update to aarch64-shenandoah-jdk8u191-b14.
- Adjust JDK-8073139/PR1758/RH1191652 to apply following 8155627 backport.
- Resolves: rhbz#1661577

* Wed Jan 09 2019 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b13-0
- Update to aarch64-shenandoah-jdk8u191-b13.
- Update tarball generation script in preparation for PR3667/RH1656676 SunEC changes.
- Use remove-intree-libraries.sh to remove the remaining SunEC code for now.
- Resolves: rhbz#1661577

* Wed Dec 19 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Fix jdk8073139-pr1758-rh1191652-ppc64_le_says_its_arch_is_ppc64_not_ppc64le_jdk.patch paths to pass git apply
- Resolves: rhbz#1633817

* Tue Nov 13 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Revise Shenandoah PR3634 patch following upstream discussion.
- Resolves: rhbz#1633817

* Wed Nov 07 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.191.b12-0
- Add missing runtime requirements for dlopened dependencies
- Add headful runtime requirement on Gtk+2 for Desktop API & look-and-feel
- Add headless runtime requirements on lksctp-tools, pcsc-ltie-devel & cups-libs
- Resolves: rhbz#1633817

* Wed Nov 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Note why PR1834/RH1022017 is not suitable to go upstream in its current form.
- Resolves: rhbz#1633817

* Mon Nov 05 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Document patch sections.
- Move JDK-8201495 to 8u192 section.
- Move JDK-8073139/PR1758/RH1191652 & JDK-8073139/PR2236/RH1191652 to 8u202 section.
- Move JDK-8044235 to 8u202 section.
- Rename patches to match other RHEL branches.
- Resolves: rhbz#1633817

* Mon Nov 05 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Fix patch organisation in the spec file:
   * Merge "Local fixes" and "RPM fixes" which amount to the same thing
   * Make it clearer that "Non-OpenJDK fixes" is currently empty
- Resolves: rhbz#1633817

* Tue Oct 09 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b12-0
- Update to aarch64-shenandoah-jdk8u191-b12.
- Resolves: rhbz#1633817

* Tue Oct 02 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.191.b10-0
- Update to aarch64-shenandoah-jdk8u191-b10.
- Drop 8146115/PR3508/RH1463098 applied upstream.
- Resolves: rhbz#1633817

* Mon Oct 01 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b16-0
- Add new Shenandoah patch PR3634 as upstream still fails on s390.
- Resolves: rhbz#1633817

* Mon Oct 01 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b16-0
- Update to aarch64-shenandoah-jdk8u181-b16.
- Drop PR3619 & PR3620 Shenandoah patches which should now be fixed upstream.
- Drop Shenandoah signedness fix as it appears in the new upstream tarball.
- Resolves: rhbz#1633817

* Thu Aug 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181.b15-0
- Move to single OpenJDK tarball build, based on aarch64/shenandoah-jdk8u.
- Update to aarch64-shenandoah-jdk8u181-b15.
- Drop 8165489-pr3589.patch which was only applied to aarch64/jdk8u builds.
- Move buildver to where it should be in the OpenJDK version.
- Split ppc64 Shenandoah fix into separate patch file with its own bug ID (PR3620).
- Update pr3539-rh1548475-pass_extra_ldflags_to_hotspot_build.patch to apply after 8187045.
- Resolves: rhbz#1633817

* Sat Aug 11 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Fix signedness build failure in shenandoahHeapRegion.cpp (upstream patch from mvala)
- Resolves: rhbz#1633817

* Sat Aug 11 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Remove unneeded functions from ppc shenandoahBarrierSet.
- Resolves: rhbz#1633817

* Wed Aug 08 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Add missing shenandoahBarrierSet implementation for ppc64{be,le}.
- Resolves: rhbz#1633817

* Tue Aug 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Fix wrong format specifiers in Shenandoah code.
- Resolves: rhbz#1633817

* Tue Aug 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Avoid changing variable types to fix size_t, at least for now.
- Resolves: rhbz#1633817

* Tue Aug 07 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- More size_t fixes for Shenandoah.
- Resolves: rhbz#1633817

* Fri Aug 03 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Add additional s390 size_t case for Shenandoah.
- Resolves: rhbz#1633817

* Fri Aug 03 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Actually add the patch...
- Resolves: rhbz#1633817

* Fri Aug 03 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Attempt to fix Shenandoah build issues on s390.
- Resolves: rhbz#1633817

* Mon Jul 23 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-4.b13
- Use the Shenandoah HotSpot on all architectures (aarch64-shenandoah-jdk8u181-b13).
- Resolves: rhbz#1633817

* Mon Jul 16 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-3.b13
- Update to aarch64-jdk8u181-b13.
- Remove 8187577/PR3578 now applied upstream.
- Resolves: rhbz#1594249

* Mon Jul 16 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181-3.b04
- Fix hook to show hs_err*.log files on failures.
- Resolves: rhbz#1594249

* Mon Jul 16 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181-3.b04
- Fix requires/provides filters for internal libs. See RHBZ#1590796
- Resolves: rhbz#1594249

* Wed Jul 11 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-2.b04
- Add "8206406, PR3610, RH1597825: StubCodeDesc constructor publishes partially-constructed objects on StubCodeDesc::_list"
- Resolves: rhbz#1594249

* Wed Jun 27 2018 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.181-1.b04
- Add hook to show hs_err*.log files on failures.
- Resolves: rhbz#1594249

* Wed Jun 27 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-1.b04
- Mark bugs that have been pushed to 8u upstream and are scheduled for a release.
- Resolves: rhbz#1594249

* Wed Jun 27 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-1.b04
- Update to aarch64-jdk8u181-b04 and aarch64-shenandoah-jdk8u181-b04.
- Resolves: rhbz#1594249

* Tue Jun 26 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.181-0.b03
- Update to aarch64-jdk8u181-b03 and aarch64-shenandoah-jdk8u181-b03.
- Remove AArch64 patch for PR3458/RH1540242 as applied upstream.
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-2.b11
- Remove build flags exemption for aarch64 now the platform is more mature and can bootstrap OpenJDK with these flags.
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-2.b11
- Fix a number of bad bug identifiers (PR3546 should be PR3578, PR3456 should be PR3546)
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-2.b11
- Split PR3458/RH1540242 fix into AArch64 & Zero sections, as their upstream trajectories differ.
- Enable patch570 missed in last changeset.
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-1.b11
- Sync with IcedTea 3.8.0.
- Label architecture-specific fixes with architecture concerned
- x86: S8199936, PR3533: HotSpot generates code with unaligned stack, crashes on SSE operations (-mstackrealign workaround)
- PR3539, RH1548475: Pass EXTRA_LDFLAGS to HotSpot build
- 8171000, PR3542, RH1402819: Robot.createScreenCapture() crashes in wayland mode
- 8197546, PR3542, RH1402819: Fix for 8171000 breaks Solaris + Linux builds
- 8185723, PR3553: Zero: segfaults on Power PC 32-bit
- 8186461, PR3557: Zero's atomic_copy64() should use SPE instructions on linux-powerpcspe
- PR3559: Use ldrexd for atomic reads on ARMv7.
- 8187577, PR3578: JVM crash during gc doing concurrent marking
- 8201509, PR3579: Zero: S390 31bit atomic_copy64 inline assembler is wrong
- 8165489, PR3589: Missing G1 barrier in Unsafe_GetObjectVolatile
- PR3591: Fix for bug 3533 doesn't add -mstackrealign to JDK code
- 8184309, PR3596: Build warnings from GCC 7.1 on Fedora 26
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.172-0.b11
- Update to aarch64-jdk8u172-b11 and aarch64-shenandoah-jdk8u172-b11.
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.171-11.b12
- Update to aarch64-jdk8u171-b12 and aarch64-shenandoah-jdk8u171-b12.
- Remove patch for 8200556/PR3566 as applied upstream.
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.171-11.b10
- Fix jconsole.desktop.in subcategory, replacing "Monitor" with "Profiling" (PR3550)
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.171-11.b10
- Fix invalid license 'LGPL+' (should be LGPLv2+ for ECC code) and add missing ones
- Resolves: rhbz#1594249

* Mon Jun 25 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.171-10.b03
- added missing hooks for c-j-c
- Resolves: rhbz#1594249

* Wed May 16 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.171-9.b10
- added and applied 1566890_embargoed20180521.patch
- Resolves: rhbz#1578548

* Mon Apr 02 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.171-4.b10
- Cleanup from previous commit.
- Resolves: rhbz#1559766

* Thu Mar 29 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.171-3.b10
- Backported from fedora: aarch64BuildFailure.patch, rhbz_1536622-JDK8197429-jdk8.patch, rhbz_1540242.patch
- Resolves: rhbz#1559766

* Sat Mar 24 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.171-0.b10
- Update to aarch64-jdk8u171-b10.
- Resolves: rhbz#1559766

* Wed Mar 21 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.162-1.b12
- Update to aarch64-jdk8u162-b12.
- Resolves: rhbz#1559766

* Wed Jan 10 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.161-4.b14
- Update to b14 with updated Zero fix for 8174962 (S8194828)
- Resolves: rhbz#1528233

* Tue Jan 09 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.161-3.b13
- Update to b13 including Zero fix for 8174962 (S8194739) and restoring tzdata2017c update
- Resolves: rhbz#1528233

* Mon Jan 08 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.161-2.b12
- Bump release due to successful build of previous version.
- Resolves: rhbz#1528233

* Mon Jan 08 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.161-1.b12
- Add new file cmsalpha.c to %%{name}-remove-intree-libraries.sh
- Resolves: rhbz#1528233

* Mon Jan 08 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.161-1.b12
- Replace tarballs with version including AArch64 fix for 8174962 (S8194686)
- Resolves: rhbz#1528233

* Mon Jan 08 2018 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.161-1.b12
- Drop pr3286-no_fp_contract.patch as flag no longer used on ppc64.
- Resolves: rhbz#1528233

* Tue Jan 02 2018 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.161-0.b12
- Update to aarch64-jdk8u161-b12 (mbalao)
- Drop upstreamed patches of:
   patch561 8075484-pr3473-rh1490713.patch
   patch532 8162384-pr3122-rh1358661.patch
   patch547 8173941-pr3326.patch
   patch554 8175887-pr3415.patch
   patch550 8180048-pr3411-rh1449870.patch
- adapted pr3286-no_fp_contract.patch, CFLAGS_linux_ppc64 no longer have -ffp-contract=off so was dropped from hunk
- Resolves: rhbz#1528233

* Wed Oct 18 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.151-2.b12
- Repack policies script adapted to new counts and paths
- Note that also c-j-c is needed to make this apply in next update
- Resolves: rhbz#1499207

* Wed Oct 18 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.151-2.b12
- Correct fix to RH1191652 root patch so existing COMMON_CCXXFLAGS_JDK is not lost.
- Resolves: rhbz#1499207

* Wed Oct 18 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.151-1.b12
- Update location of policy JAR files following 8157561.
- Resolves: rhbz#1499207

* Tue Oct 17 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.151-1.b12
- Update SystemTap tapsets to version in IcedTea 3.6.0pre02 to fix RH1492139.
- Resolves: rhbz#1499207

* Tue Oct 17 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.151-1.b12
- Fix premature shutdown of NSS in SunEC provider.
- Move -ffp-no-contract fix to local fixes section.
- Resolves: rhbz#1499207

* Tue Oct 17 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.151-1.b12
- Add 8075484/PR3473/RH1490713 which is listed as being in 8u151 but not supplied by Oracle.
- Resolves: rhbz#1499207

* Tue Oct 17 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.151-1.b12
- Update to aarch64-jdk8u151-b12.
- Update location of OpenJDK zlib system library source code in remove-intree-libraries.sh
- Drop upstreamed patches for 8179084 and RH1367357 (part of 8183028).
- Update RH1191652 (root) to accomodate 8151841 (GCC 6 support).
- Update RH1163501 to accomodate 8181048 (crypto refactoring)
- Resolves: rhbz#1499207

* Tue Aug 15 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.144-1.b01
- Update to aarch64-jdk8u144-b01.
- Resolves: rhbz#1477858

* Fri Jul 14 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.141-2.b16
- Update to aarch64-jdk8u141-b16.
- Revert change to remove-intree-libraries.sh following backout of 8173207
- Resolves: rhbz#1466509

* Wed Jul 05 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.141-1.b15
- Update to aarch64-jdk8u141-b15.
- Update location of OpenJDK system library source code in remove-intree-libraries.sh
- Drop upstreamed patches for 6515172, 8144566, 8155049, 8165231, 8174164, 8174729 and 8175097.
- Update PR1983, PR2899 and PR2934 (SunEC + system NSS) to accomodate 8175110.
- Resolves: rhbz#1466509

* Wed Jul 05 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.131-3.b12
- Add backports from 8u152 (8179084/RH1455694, 8175887) ahead of July CPU.
- Resolves: rhbz#1466509

* Tue Jul 04 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.131-2.b11
- Backport "8180048: Interned string and symbol table leak memory during parallel unlinking"
- Resolves: rhbz#1449870

* Thu Apr 13 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.131-1.b11
- Update to aarch64-jdk8u131-b11.
- Drop upstreamed patches for 8147910, 8161993, 8170888 and 8173783.
- Update generate_source_tarball.sh to remove patch remnants.
- Cleanup tarball creation documentation to avoid duplication.
- Resolves: rhbz#1438751

* Fri Apr 07 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.121-3.b13
- Add backports from 8u131 and 8u152 ahead of April CPU.
- Apply backports before local RPM fixes so they will be the same as when applied upstream
- Adjust RH1022017 following application of 8173783
- Bump release by 2 for y-stream branch.
- Resolves: rhbz#1438751

* Mon Jan 16 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.121-1.b13
- Update to aarch64-jdk8u121-b13.
- Add MD5 checksum for the new java.security file (EC < 224, DSA < 1024 restricted)
- Resolves: rhbz#1410612

* Mon Jan 16 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.112-1.b16
- Update to aarch64-jdk8u112-b16.
- Drop upstreamed patches for 8044762, 8049226, 8154210, 8158260 and 8160122.
- Re-generate size_t and key size (RH1163501) patches against u112.
- Resolves: rhbz#1410612

* Mon Jan 16 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-6.b14
- Enable a full bootstrap on JIT archs to ensure stability.
- Resolves: rhbz#1410612

* Mon Jan 16 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-5.b18
- Disable -ffp-no-contract option introduced by 8170873 as not available on RHEL 6 GCC.
- Resolves: rhbz#1410612

* Thu Jan 12 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-5.b18
- Use java-1.7.0-openjdk to bootstrap on RHEL to allow us to use main build target
- Resolves: rhbz#1410612

* Mon Jan 09 2017 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-5.b18
- Update to aarch64-jdk8u111-b18, synced with upstream u111, S8170873 and new AArch64 fixes
- Replace our correct version of 8159244 with the amendment to the 8u version from 8160122.
- Resolves: rhbz#1410612

* Mon Nov 07 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-4.b15
- Add fix for PR2934 / RH1329342
- Resolves: rhbz#1391682

* Mon Oct 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-3.b15
- Restrict debug builds to shipped JIT architectures, excluding unshipped ppc64
- Resolves: rhbz#1381990

* Mon Oct 10 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.111-2.b15
- added nss restricting requires
- Resolves: rhbz#1381990

* Mon Oct 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-1.b15
- Turn debug builds on for all JIT architectures. Always AssumeMP on RHEL.
- Resolves: rhbz#1381990

* Fri Oct 07 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-1.b15
- Update to aarch64-jdk8u111-b15, with AArch64 fix for S8160591.
- Resolves: rhbz#1381990

* Fri Oct 07 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.111-1.b14
- Update to aarch64-jdk8u111-b14.
- Drop the CORBA typo fix, which appears upstream in u111.
- Add LCMS 2 patch to fix Red Hat security issue RH1367357 in the local OpenJDK copy.
- Resolves: rhbz#1381990

* Tue Aug 30 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.102-2.b14
- New variable, @prefix@, needs to be substituted in tapsets (rhbz1371005)
- Resolves: rhbz#1381990

* Tue Aug 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.102-1.b14
- Update to aarch64-jdk8u102-b14.
- Drop 8140620, 8148752 and 6961123, all of which appear upstream in u102.
- Move 8159244 to 8u111 section as it only appears to be in unpublished u102 b31.
- Move 8158260 to 8u112 section following its backport to 8u.
- Resolves: rhbz#1381990

* Tue Aug 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-7.b15
- Update to aarch64-jdk8u101-b15.
- Rebase SystemTap tarball on IcedTea 3.1.0 versions so as to avoid patching.
- Drop additional hunk for 8147771 which is now applied upstream.
- Resolves: rhbz#1381990

* Mon Aug 15 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-6.b13
- Make all architectures depend on java-1.8.0-openjdk again for building.
- Resolves: rhbz#1163378

* Mon Aug 15 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-5.b13
- Enable an unshipped ppc64 RPM, initially depending on java-1.7.0-openjdk to build.
- Resolves: rhbz#1163378

* Mon Jul 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-4.b13
- Replace bad 8159244 patch from upstream 8u with fresh backport from OpenJDK 9.
- Resolves: rhbz#1350035

* Sun Jul 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-3.b13
- Add missing hunk from 8147771, missed due to inclusion of unneeded 8138811
- Resolves: rhbz#1350035

* Mon Jul 04 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-2.b13
- Add workaround for a typo in the CORBA security fix, 8079718
- Resolves: rhbz#1350035

* Fri Jul 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-1.b13
- Update to u101b13.
- Backport REPOS option in generate_source_tarball.sh
- Drop a leading zero from the priority as the update version is now three digits
- Resolves: rhbz#1350035

* Fri Jul 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.92-0.b14
- Add additional fixes (S6260348, S8159244) for u92 update.
- Resolves: rhbz#1350035

* Fri Jul 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.92-0.b14
- Update ppc64le fix with upstream version, S8158260.
- Resolves: rhbz#1350035

* Fri Jul 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.92-0.b14
- Add fix for ppc64le crash due to illegal instruction.
- Resolves: rhbz#1350035

* Fri Jul 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.92-0.b14
- Add backport for S8148752.
- Resolves: rhbz#1350035

* Fri Jul 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.92-0.b14
- Update to u92b14.
- Remove upstreamed patches for Zero build failures 8087120 & 8143855.
- Add 8132051 Zero fix upstreamed as 8154210 in 8u112.
- Add upstreamed patch 6961123 from u102 to fix application name in GNOME Shell.
- Add upstreamed patches 8044762 & 8049226 from u112 to fix JDI issues.
- Regenerate pr1758-rh1191652-ppc64_le_says_its_arch_is_ppc64_not_ppc64le_root.patch against u92
- Resolves: rhbz#1350035

* Tue Jun 21 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-4.b14
- Bump release to 4 so it remains greater than 6.8.z.
- Resolves: rhbz#1022017

* Thu Jun 02 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-2.b14
- Forwardport SSL fix to only report curves supported by NSS.
- Resolves: rhbz#1022017

* Sun Apr 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Use basename of test file to avoid misinterpretation of full path as a package
- Resolves: rhbz#1325421

* Sun Apr 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Update to u91b14.
- Resolves: rhbz#1325421

* Thu Mar 31 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add ECDSA test to ensure ECC is working.
- Resolves: rhbz#1325421

* Wed Mar 30 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-2.b03
- Avoid WithSeed versions of NSS functions as they do not fully process the seed
- Resolves: rhbz#1320662

* Fri Mar 25 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- Revert previous change to CFLAGS/LDFLAGS as issue is not us, but rhbz#1320961
- Resolves: rhbz#1320662

* Wed Mar 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- Disable RPM CFLAGS/LDFLAGS for now due to build issues.
- Resolves: rhbz#1320662

* Wed Mar 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- RHEL 6 adds -fasynchronous-unwind-tables which leads to libjvm.so being too big on x86
- Resolves: rhbz#1320662

* Wed Mar 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- Remove patches to generated configure script, which we re-generate anyway.
- Resolves: rhbz#1320662

* Wed Mar 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- Update to u77b03.
- Drop 8146566 which is applied upstream.
- Replace s390 Java options patch with general version from IcedTea.
- Apply s390 patches unconditionally to avoid arch-specific patch failures.
- Remove fragment of s390 size_t patch that unnecessarily removes a cast, breaking ppc64le.
- Remove aarch64-specific suffix as update/build version are now the same as for other archs.
- Only use z format specifier on s390, not s390x.
- Adjust tarball generation script to allow ecc_impl.h to be included.
- Correct spelling mistakes in tarball generation script.
- Synchronise minor changes from Fedora.
- Use a simple backport for PR2462/8074839.
- Don't backport the crc check for pack.gz. It's not tested well upstream.
- Resolves: rhbz#1320662

* Thu Feb 04 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.71-5.b17
- returned jre_versionless_lnk/bin instead of jrebindir and
-   and    sdk_versionless_lnk/bin isntead of sdkbindir
- Resolves: rhbz#1295752

* Wed Jan 27 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-4.b15
- Add patches to allow the SunEC provider to be built with the system NSS install.
- Re-generate source tarball so it includes ecc_impl.h.
- Adjust tarball generation script to allow ecc_impl.h to be included.
- Bring over NSS changes from java-1.7.0-openjdk spec file (NSS_CFLAGS/NSS_LIBS/headers)
- Remove patch which disables the SunEC provider as it is now usable.
- Resolves: rhbz#1208307

* Thu Jan 14 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-3.b15
- Add patch to turn off strict overflow on IndicRearrangementProcessor{,2}.cpp
- Resolves: rhbz#1295752

* Wed Jan 13 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-2.b15
- RHEL 6 does not have __global_ldflags so set to %%{nil} instead.
- Resolves: rhbz#1295752

* Wed Jan 13 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-2.b15
- Remove -Wno-cpp which is not supported on RHEL 6 gcc.
- Resolves: rhbz#1295752

* Wed Jan 13 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-2.b15
- Try enabling the RPM CFLAGS and LDFLAGS.
- Resolves: rhbz#1295752

* Wed Jan 13 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-1.b15
- January 2016 security update to u71b15.
- Improve verbosity and helpfulness of tarball generation script.
- Update patch documentation using version originally written for Fedora.
- Drop prelink requirement as we no longer use execstack.
- Drop ifdefbugfix patch as this is fixed upstream.
- Provide optional boostrap build and turn it off by default.
- Add patch for size_t formatting on s390 as size_t != intptr_t there.
- Resolves: rhbz#1295752

* Wed Jan 13 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-5.b17
- Add flag logic back to spec file but disable for now.
- Restore jdk8042159-allow_using_system_installed_lcms2.patch as used in October CPU.
- Resolves: rhbz#1295752

* Tue Jan 12 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-4.b17
- moved to integration forest 
- sync with rhel7
- Resolves: rhbz#1295752

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-2.b17
- Add patch to honour %%{_smp_ncpus_max} from Tuomo Soini
- Resolves: rhbz#1152896

* Tue Dec 08 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-1.b17
- Bump to distinguish this from the z-stream release.
- Resolves: rhbz#1257655

* Thu Oct 15 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-0.b17
- October 2015 security update to u65b17.
- Add script for generating OpenJDK tarballs from a local Mercurial tree.
- Update RH1191652 patch to build against current AArch64 tree.
- Use appropriate source ID to avoid unpacking both tarballs on AArch64.
- Fix library removal script so jpeg, giflib and png sources are removed.
- Update jdk8042159-allow_using_system_installed_lcms2.patch to regenerated upstream (8042159) version.
- Drop LCMS update from rh1649731-allow_to_build_on_rhel6_with_stdcpplib_autotools_2_63.patch
- Resolves: rhbz#1257655

* Fri Sep 04 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-4.b27
- updated to u60 (1255352)
- Resolves: rhbz#1257655

* Fri Sep 04 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.51-5.b16
- direcotries aligned to rhel6, jdk7 like style ifarch 64 name.arch else naem
- moved to rhel7, jdk8 like style of name.arch. Fixes 1259241
- Resolves: rhbz#1251560

* Fri Aug 21 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.51-4.b16
- Backport S8017773: OpenJDK7 returns incorrect TrueType font metrics
- Resolves: rhbz#1239063

* Thu Aug 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.51-3.b16
- priority aligned with other openjdks to 7
- another touching attempt to polycies...
- Resolves: rhbz#1251560

* Thu Aug 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.51-2.b16
- main links in alternatives moved to versionless format
- Resolves: rhbz#1217177

* Thu Jul 02 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.51-1.b16
- Bump release number so 6.7 version is greater than 6.6
- Resolves: rhbz#1235161

* Thu Jul 02 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.51-0.b16
- July 2015 security update to u51b16.
- Add script for generating OpenJDK tarballs from a local Mercurial tree.
- Add %%{name} prefix to patches to avoid conflicts with OpenJDK 7 versions.
- Add patches for RH issues fixed in IcedTea 2.x and/or the upcoming u60.
- Use 'openjdk' as directory prefix to allow patch interchange with IcedTea.
- Re-generate EC disablement patch following CPU DH changes.
- Resolves: rhbz#1235161

* Wed Apr 29 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-35.b13
- Omit jsa files from power64 file list as well, as they are never generated
- Use the template interpreter on ppc64le
- priority set  gcj < lengthOffFour < otherJdks (RH1175457)
- misusing already fixed bug
- Resolves: rhbz#1189853

* Fri Apr 17 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.45-31.b13
- Make use of system timezone data for OpenJDK 8.
- Resolves: rhbz#1212592

* Fri Apr 10 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-30.b13
- repacked sources
- Resolves: RHBZ#1209075

* Thu Apr 09 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-29.b13
- do not obsolete openjdk7
- Resolves: rhbz#1209075

* Tue Apr 07 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.45-27.b13
- Add back ExclusiveArch declaration lost in merge.
- Fix names of PStack patch and removal script to not clash with 7 versions.
- Remove unneeded test case from RHEL 7 ppc64le bug.
- Resolves: rhbz#1209075

* Tue Apr 07 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-27.b13
- updated to security u45
- minor sync with 6.7
 - generate_source_tarball.sh
 - adapted jdk8201495-zero_reduce_limits_of_max_heap_size_for_boot_JDK_on_s390.patch and jdk8203030-zero_s390_31_bit_size_t_type_conflicts_in_shared_code.patch
 - reworked (synced) zero patches (removed 103,11 added 204, 400-403)
 - added upstreamed patch 501 and 505
 - included removeSunEcProvider-RH1154143.patch
- returned java (jre only) provides
- repacked policies (source20)
- removed duplicated NVR provides
- added automated test for priority (length7)
- Resolves: RHBZ#1209075

Fri Jan 09 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.31-1.b13
- Update to January CPU patch update.
- Resolves: RHBZ#1180300

* Fri Oct 24 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.25-4.b17
- updated aarch64 sources
- epoch synced to 1
- all ppcs excluded from classes dump(1156151)
- removed duplicated provides
- Resolves: rhbz#1146622

* Fri Oct 24 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.25-3.b17
- added patch12,removeSunEcProvider-RH1154143
- xdump excluded from ppc64le (rh1156151)
- Add check for src.zip completeness. See RH1130490 (by sgehwolf@redhat.com)
- Resolves: rhbz#1154143

* Wed Oct 22 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.25-3.b17
- Do not provide any JPackage-style java* provides.
- Resolves: RHBZ#1155783

* Mon Oct 20 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.25-2.b17
- ec/impl removed from source tarball
- Resolves: RHBZ#1154143

* Mon Oct 06 2014 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.25-1.b17
- Update to October CPU patch update.
- Resolves: RHBZ#1148896

* Fri Sep 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-3.b26
- fixed headless (policytool moved to normal)
 - jre/bin/policytool added to not headless exclude list
- updated aarch694 source
- ppc64le synced from fedora
- Resolves: rhbz#1081073

* Mon Sep 08 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-2.b26
- forcing build by itself (jdk8 by jdk8)
- Resolves: rhbz#1081073

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-1.b26
- updated to u20-b26
- adapted patch9999 enableArm64.patch
- adapted patch100 s390-java-opts.patch
- adapted patch102 size_t.patch
- removed upstreamed patch  0001-PPC64LE-arch-support-in-openjdk-1.8.patch
- adapted  jdk8042159-allow_using_system_installed_lcms2.patch
- removed patch8 set-active-window.patch
- removed patch9 javadoc-error-jdk-8029145.patch
- removed patch10 javadoc-error-jdk-8037484.patch
- removed patch99 applet-hole.patch - itw 1.5.1 is able to ive without it
- Resolves: rhbz#1081073

* Tue Aug 19 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-19.b12
- fixed desktop icons
- Icon set to java-1.8.0
- Development removed from policy tool
- Resolves: rhbz#1081073

* Thu Aug 14 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-18.b12
- fixed jstack
- Resolves: rhbz#1081073

* Thu Aug 14 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-15.b12
- fixed provides/obsolates
- Resolves: rhbz#1081073

* Thu Aug 14 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-14.b12
- mayor rework of specfile - sync with f21
 - accessibility kept removed
 - lua script kept unsync
 - priority and epoch kept on 0
 - not included disable-doclint patch
 - kept bundled lcms
 - unused OrderWithRequires
 - used with-stdcpplib instead of with-stdc++lib
- Resolves: rhbz#1081073

* Wed Jul 09 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-4.b13
- Added security patches
- Resolves: rhbz#1081073

* Wed Jul 02 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.5-6.b13
- Removed accessibility package
 - removed patch3 java-atk-wrapper-security.patch
 - removed its files and declaration
 - removed creation of libatk-wrapper.so and java-atk-wrapper.jar symlinks
 - removed generation of accessibility.properties
- Resolves: rhbz#1113078

* Fri May 16 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.5-5.b13
- priority lowered to 00000
- Resolves: rhbz#1081073

* Mon Apr 28 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.5-4.b13
- Initial import from fedora
- Used bundled lcms2
 - added java-1.8.0-openjdk-disable-jdk8042159-allow_using_system_installed_lcms2.patch
 - --with-lcms changed to bundled
 - removed build requirement
 - excluded removal of lcms from remove-intree-libraries.sh
- removed --with-extra-cflags="-fno-devirtualize" and --with-extra-cxxflags="-fno-devirtualize"--- 
- added patch998, rh1649731-allow_to_build_on_rhel6_with_stdcpplib_autotools_2_63.patch  to
 - fool autotools
 - replace all ++ chars in autoconfig files by pp
- --with-stdc++lib=dynamic  replaced by --with-stdcpplib=dynamic 
- Bumped release
- Set epoch to 0
- removed patch6, disable-doclint-by-default.patch
- Resolves: rhbz#1081073
