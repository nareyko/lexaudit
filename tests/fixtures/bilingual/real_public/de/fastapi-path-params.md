# Pfad-Parameter  

Sie können Pfad-„Parameter“ oder -„Variablen“ mit der gleichen Syntax deklarieren, welche in Python- Formatstrings  verwendet wird:

 

Der Wert des Pfad-Parameters   wird Ihrer Funktion als das Argument   übergeben.

Wenn Sie also dieses Beispiel ausführen und auf   gehen, sehen Sie als  Response :

 

## Pfad-Parameter mit Typen  

Sie können den Typ eines Pfad-Parameters in der Funktion deklarieren, mit Standard-Python-Typannotationen:

 

In diesem Fall wird   als   deklariert.

 

Dadurch erhalten Sie Editor-Unterstützung innerhalb Ihrer Funktion, mit Fehlerprüfungen, Codevervollständigung, usw.

 
## Daten- Konversion   

Wenn Sie dieses Beispiel ausführen und Ihren Browser unter   öffnen, sehen Sie als Response:

 

 

Beachten Sie, dass der Wert, den Ihre Funktion erhalten (und zurückgegeben) hat,   ist, als Python- , nicht als String  .

Sprich, mit dieser Typdeklaration bietet **FastAPI** Ihnen automatisches Request- „Parsing“ .

 
## Datenvalidierung  

Wenn Sie aber im Browser   besuchen, erhalten Sie eine hübsche HTTP-Fehlermeldung:

 

denn der Pfad-Parameter   hatte den Wert  , was kein   ist.

Die gleiche Fehlermeldung würde angezeigt werden, wenn Sie ein   statt eines  s übergeben würden, wie etwa in:  

 

Sprich, mit der gleichen Python-Typdeklaration gibt Ihnen **FastAPI** Datenvalidierung.

Beachten Sie, dass die Fehlermeldung auch direkt die Stelle anzeigt, wo die Validierung nicht erfolgreich war.

Das ist unglaublich hilfreich, wenn Sie Code entwickeln und debuggen, welcher mit Ihrer API interagiert.

 
## Dokumentation  

Und wenn Sie die Seite   in Ihrem Browser öffnen, sehen Sie eine automatische, interaktive API-Dokumentation wie:

 

 

Wiederum, nur mit dieser gleichen Python-Typdeklaration gibt Ihnen **FastAPI** eine automatische, interaktive Dokumentation (integriert Swagger UI).

Beachten Sie, dass der Pfad-Parameter dort als Ganzzahl deklariert ist.

 
## Standardbasierte Vorteile, alternative Dokumentation  

Und weil das generierte Schema vom OpenAPI-Standard kommt, gibt es viele kompatible Tools.

Aus diesem Grund bietet **FastAPI** selbst eine alternative API-Dokumentation (verwendet ReDoc), welche Sie unter   einsehen können:

 

Auf die gleiche Weise gibt es viele kompatible Tools. Inklusive Codegenerierungstools für viele Sprachen.

## Pydantic  

Die ganze Datenvalidierung wird hinter den Kulissen von Pydantic durchgeführt, Sie profitieren also von dessen Vorteilen. Und Sie wissen, dass Sie in guten Händen sind.

Sie können die gleichen Typdeklarationen auch mit  ,  ,   und vielen anderen komplexen Datentypen verwenden.

Mehrere davon werden in den nächsten Kapiteln des Tutorials erkundet.

## Die Reihenfolge ist wichtig

