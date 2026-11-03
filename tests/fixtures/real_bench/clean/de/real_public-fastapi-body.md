# Requestbody  

Wenn Sie Daten von einem  Client  (sagen wir, einem Browser) zu Ihrer API senden müssen, senden Sie sie als **Requestbody**.

Ein  **Request**body  sind Daten, die vom Client zu Ihrer API gesendet werden. Ein  **Response**body  sind Daten, die Ihre API zum Client sendet.

Ihre API muss fast immer einen **Response**body senden. Aber Clients müssen nicht unbedingt immer **Requestbodys** senden, manchmal fordern sie nur einen Pfad an, vielleicht mit einigen Query-Parametern, aber senden keinen Body.

Um einen **Request**body zu deklarieren, verwenden Sie Pydantic-Modelle mit all deren Fähigkeiten und Vorzügen.

 

Um Daten zu senden, sollten Sie eines von:   (meistverwendet),  ,   oder   verwenden.

Das Senden eines Bodys mit einem  -Request hat ein undefiniertes Verhalten in den Spezifikationen, wird aber dennoch von FastAPI unterstützt, nur für sehr komplexe/extreme Anwendungsfälle.

Da davon abgeraten wird, zeigt die interaktive Dokumentation mit Swagger UI die Dokumentation für den Body nicht an, wenn   verwendet wird, und zwischengeschaltete Proxys unterstützen es möglicherweise nicht.

 
## Pydantics   importieren  

Zuerst müssen Sie   von   importieren:

 

## Ihr Datenmodell erstellen  

Dann deklarieren Sie Ihr Datenmodell als eine Klasse, die von   erbt.

Verwenden Sie Standard-Python-Typen für alle Attribute:

 

Wie auch bei der Deklaration von Query-Parametern gilt: Wenn ein Modellattribut einen Defaultwert hat, ist das Attribut nicht erforderlich. Andernfalls ist es erforderlich. Verwenden Sie  , um es einfach optional zu machen.

Zum Beispiel deklariert das obige Modell ein JSON „ “ (oder Python-   ) wie dieses:

 

... da   und   optional sind (mit   als Defaultwert), wäre dieses JSON „ “ ebenfalls gültig:

 

## Als Parameter deklarieren  

Um es zu Ihrer *Pfadoperation* hinzuzufügen, deklarieren Sie es auf die gleiche Weise, wie Sie Pfad- und Query-Parameter deklariert haben:

 

... und deklarieren Sie dessen Typ als das Modell, welches Sie erstellt haben,  .

## Resultate  

Mit nur dieser Python-Typdeklaration wird **FastAPI**:

