; Custom NSIS hooks for Zero-Employee Orchestrator
; Persists the installer-selected language so the app can use the same locale.

!macro NSIS_HOOK_POSTINSTALL
  ; Map NSIS language ID ($LANGUAGE) to locale code and write to file.
  ; The app reads this file on first launch to match the installer language.
  StrCmp $LANGUAGE 1041 0 +3
    FileOpen $0 "$INSTDIR\installer_locale.txt" w
    FileWrite $0 "ja"
    FileClose $0
    Goto done_locale
  StrCmp $LANGUAGE 2052 0 +3
    FileOpen $0 "$INSTDIR\installer_locale.txt" w
    FileWrite $0 "zh"
    FileClose $0
    Goto done_locale
  StrCmp $LANGUAGE 1042 0 +3
    FileOpen $0 "$INSTDIR\installer_locale.txt" w
    FileWrite $0 "ko"
    FileClose $0
    Goto done_locale
  StrCmp $LANGUAGE 1046 0 +3
    FileOpen $0 "$INSTDIR\installer_locale.txt" w
    FileWrite $0 "pt"
    FileClose $0
    Goto done_locale
  StrCmp $LANGUAGE 1055 0 +3
    FileOpen $0 "$INSTDIR\installer_locale.txt" w
    FileWrite $0 "tr"
    FileClose $0
    Goto done_locale
  ; Default: English
  FileOpen $0 "$INSTDIR\installer_locale.txt" w
  FileWrite $0 "en"
  FileClose $0
  done_locale:
!macroend
