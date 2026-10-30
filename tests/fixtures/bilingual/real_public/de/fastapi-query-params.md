# Query-Parameter  

Wenn Sie in Ihrer Funktion andere Parameter deklarieren, die nicht Teil der Pfad-Parameter sind, dann werden diese automatisch als „Query“-Parameter interpretiert.

 

Die  Query  ist die Menge von Schlüssel-Wert-Paaren, die nach dem   in einer URL folgen und durch  -Zeichen getrennt sind.

Zum Beispiel sind in der URL:

 

... die Query-Parameter:

*  : mit dem Wert  
*  : mit dem Wert  

Da sie Teil der URL sind, sind sie „naturgemäß“ Strings.

Aber wenn Sie sie mit Python-Typen deklarieren (im obigen Beispiel als  ), werden sie zu diesem Typ konvertiert und gegen diesen validiert.

Die gleichen Prozesse, die für Pfad-Parameter gelten, werden auch auf Query-Parameter angewendet:

* Editor-Unterstützung (natürlich)
* Daten- „Parsen“ 
* Datenvalidierung
* Automatische Dokumentation

## Defaultwerte  

Da Query-Parameter kein fester Teil eines Pfades sind, können sie optional sein und Defaultwerte haben.

Im obigen Beispiel haben sie die Defaultwerte   und  .

Wenn Sie also zur URL:

 

gehen, so ist das das gleiche wie die URL:

 

Aber wenn Sie zum Beispiel zu:

 

gehen, werden die Parameterwerte Ihrer Funktion sein:

*  : da Sie das in der URL gesetzt haben
*  : weil das der Defaultwert ist

## Optionale Parameter  

Auf die gleiche Weise können Sie optionale Query-Parameter deklarieren, indem Sie deren Defaultwert auf   setzen:

 

In diesem Fall wird der Funktionsparameter   optional und standardmäßig   sein.

 

Beachten Sie auch, dass **FastAPI** intelligent genug ist, um zu erkennen, dass der Pfad-Parameter   ein Pfad-Parameter ist und   keiner, daher muss letzteres ein Query-Parameter sein.

 
## Typkonvertierung von Query-Parametern  

Sie können auch  -Typen deklarieren, und sie werden konvertiert:

 

Wenn Sie in diesem Fall zu:

 

oder

 

oder

 

oder

 

oder

 

gehen, oder zu irgendeiner anderen Variante der Groß-/Kleinschreibung (Alles groß, Anfangsbuchstabe groß, usw.), dann wird Ihre Funktion den Parameter   mit dem  -Wert   sehen, ansonsten mit dem Wert  .

## Mehrere Pfad- und Query-Parameter  

Sie können mehrere Pfad-Parameter und Query-Parameter gleichzeitig deklarieren, **FastAPI** weiß, welches welcher ist.

Und Sie müssen sie auch nicht in einer spezifischen Reihenfolge deklarieren.

Parameter werden anhand ihres Namens erkannt:

 

## Erforderliche Query-Parameter  

Wenn Sie einen Defaultwert für Nicht-Pfad-Parameter deklarieren (bis jetzt haben wir nur Query-Parameter gesehen), dann ist der Parameter nicht erforderlich.

Wenn Sie keinen spezifischen Wert haben wollen, sondern der Parameter einfach optional sein soll, dann setzen Sie den Defaultwert auf  .

Aber wenn Sie wollen, dass ein Query-Parameter erforderlich ist, vergeben Sie einfach keinen Defaultwert:

