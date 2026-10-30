# Erste Schritte  

Die einfachste FastAPI-Datei könnte wie folgt aussehen:

 

Kopieren Sie das in eine Datei  .

 

FastAPI hat eine offizielle Erweiterung für VS Code (und Cursor), die viele Features bereitstellt, darunter einen Pfadoperation-Explorer, Pfadoperation-Suche, CodeLens-Navigation in Tests (Sprung zur Definition aus Tests) sowie Deployment und Logs von FastAPI Cloud, alles aus Ihrem Editor heraus.

 

 

 

 

In der Konsolenausgabe sollte es eine Zeile geben, die ungefähr so aussieht:

 

Diese Zeile zeigt die URL, unter der Ihre App auf Ihrem lokalen Computer bereitgestellt wird.

### Es testen  

Öffnen Sie Ihren Browser unter  

Sie werden die JSON- Response  sehen:

 

### Interaktive API-Dokumentation  

Gehen Sie als Nächstes auf  

Sie werden die automatisch erzeugte, interaktive API-Dokumentation sehen (bereitgestellt durch Swagger UI):

 

### Alternative API-Dokumentation  

Gehen Sie nun auf  

Dort sehen Sie die alternative, automatische Dokumentation (bereitgestellt durch ReDoc):

 

### OpenAPI  

**FastAPI** generiert ein „Schema“ mit all Ihren APIs unter Verwendung des **OpenAPI**-Standards zur Definition von APIs.

#### „Schema“  

Ein „Schema“ ist eine Definition oder Beschreibung von etwas. Nicht der eigentliche Code, der es implementiert, sondern lediglich eine abstrakte Beschreibung.

#### API-„Schema“  

In diesem Fall ist OpenAPI eine Spezifikation, die vorschreibt, wie ein Schema für Ihre API zu definieren ist.

Diese Schemadefinition enthält Ihre API-Pfade, die möglichen Parameter, welche diese entgegennehmen, usw.

#### Daten-„Schema“  

Der Begriff „Schema“ kann sich auch auf die Form von Daten beziehen, wie z. B. einen JSON-Inhalt.

In diesem Fall sind die JSON-Attribute und deren Datentypen, usw. gemeint.

#### OpenAPI und JSON Schema  

OpenAPI definiert ein API-Schema für Ihre API. Dieses Schema enthält Definitionen (oder „Schemas“) der Daten, die von Ihrer API unter Verwendung von **JSON Schema**, dem Standard für JSON-Datenschemata, gesendet und empfangen werden.

#### Die   testen  

Falls Sie wissen möchten, wie das rohe OpenAPI-Schema aussieht: FastAPI generiert automatisch ein JSON (Schema) mit den Beschreibungen Ihrer gesamten API.

Sie können es direkt einsehen unter:  

Es wird ein JSON angezeigt, welches ungefähr so aussieht:

 

#### Wofür OpenAPI gedacht ist  

Das OpenAPI-Schema ist die Grundlage für die beiden enthaltenen interaktiven Dokumentationssysteme.

Es gibt dutzende Alternativen, die alle auf OpenAPI basieren. Sie können jede dieser Alternativen problemlos zu Ihrer mit **FastAPI** erstellten Anwendung hinzufügen.

