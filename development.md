# Developer Guide

## Init app

1. ```poetry install```
2. ```alembic upgrade head```



### Translations

```commandline
$pyFiles = Get-ChildItem .\src\app\desktop_client\ -Recurse -Filter *.py | Select-Object -ExpandProperty FullName

pylupdate6 @pyFiles -ts translations\app_ru.ts --verbose
pylupdate6 @pyFiles -ts translations\app_en.ts --verbose

pyside6-lrelease translations/app_ru.ts -qm translations/app_ru.qm    
pyside6-lrelease translations/app_en.ts -qm translations/app_en.qm    
```

