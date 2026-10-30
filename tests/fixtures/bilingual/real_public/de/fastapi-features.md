# Merkmale  

## FastAPI-Merkmale  

**FastAPI** ermöglicht Ihnen Folgendes:

### Auf offenen Standards basieren  

* **OpenAPI** für die Erstellung von APIs, inklusive Deklarationen von  Pfad - Operationen , Parametern,  Requestbodys , Sicherheit, usw.
* Automatische Dokumentation der Datenmodelle mit **JSON Schema** (da OpenAPI selbst auf JSON Schema basiert).
* Um diese Standards herum entworfen, nach sorgfältigem Studium. Statt einer nachträglichen Schicht darüber.
* Dies ermöglicht auch automatische **Client-Code-Generierung** in vielen Sprachen.

### Automatische Dokumentation  

Interaktive API-Dokumentation und erkundbare Web-Benutzeroberflächen. Da das Framework auf OpenAPI basiert, gibt es mehrere Optionen, zwei sind standardmäßig vorhanden.

* **Swagger UI**, mit interaktiver Erkundung, rufen Sie Ihre API direkt vom Browser aus auf und testen Sie sie.

 

* Alternative API-Dokumentation mit **ReDoc**.

 

### Nur modernes Python  

Alles basiert auf Standard-**Python-Typ**deklarationen (dank Pydantic). Es muss keine neue Syntax gelernt werden. Nur modernes Standard-Python.

Wenn Sie eine zweiminütige Auffrischung benötigen, wie man Python-Typen verwendet (auch wenn Sie FastAPI nicht benutzen), schauen Sie sich das kurze Tutorial an: Python-Typen.

Sie schreiben Standard-Python mit Typen:

 

Das kann nun wie folgt verwendet werden:

 

 

  bedeutet:

Übergeben Sie die Schlüssel und Werte des    Dicts  direkt als Schlüssel-Wert-Argumente, äquivalent zu:  

 
### Editorunterstützung  

Das ganze Framework wurde so entworfen, dass es einfach und intuitiv zu benutzen ist; alle Entscheidungen wurden auf mehreren Editoren getestet, sogar vor der Implementierung, um die bestmögliche Entwicklererfahrung zu gewährleisten.

In den Python-Entwickler-Umfragen wird klar, dass die meist genutzte Funktion die „Autovervollständigung“ ist.

Das gesamte **FastAPI**-Framework ist darauf ausgelegt, das zu erfüllen. Autovervollständigung funktioniert überall.

Sie werden selten noch mal in der Dokumentation nachschauen müssen.

So kann Ihr Editor Sie unterstützen:

* in Visual Studio Code:

 

* in PyCharm:

 

Sie bekommen sogar Autovervollständigung an Stellen, an denen Sie dies vorher nicht für möglich gehalten hätten. Zum Beispiel der  -Schlüssel innerhalb eines JSON-Bodys (dieser könnte auch verschachtelt sein), der aus einem Request kommt.

Nie wieder falsche Schlüsselnamen tippen, Hin und Herhüpfen zwischen der Dokumentation, Hoch- und Runterscrollen, um herauszufinden, ob es   oder   war.

### Kompakt  

Es gibt für alles sinnvolle **Defaultwerte**, mit optionaler Konfiguration überall. Alle Parameter können feinjustiert werden, damit sie tun, was Sie benötigen, und die API definieren, die Sie brauchen.

