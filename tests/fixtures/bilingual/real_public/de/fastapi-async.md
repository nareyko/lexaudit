# Nebenläufigkeit und async / await  

Details zur  -Syntax für *Pfadoperation-Funktionen* und Hintergrundinformationen zu asynchronem Code, Nebenläufigkeit und Parallelität.

## In Eile?  

  TL;DR:  

Wenn Sie Bibliotheken von Dritten verwenden, die mit   aufgerufen werden müssen, wie zum Beispiel:

 

Dann deklarieren Sie Ihre *Pfadoperation-Funktionen* mit  , wie in:

 

 

Sie können   nur innerhalb von Funktionen verwenden, die mit   erstellt wurden.

 
---

Wenn Sie eine Bibliothek eines Dritten verwenden, die mit etwas kommuniziert (einer Datenbank, einer API, dem Dateisystem, usw.) und welche die Verwendung von   nicht unterstützt (dies ist derzeit bei den meisten Datenbankbibliotheken der Fall), dann deklarieren Sie Ihre *Pfadoperation-Funktionen* ganz normal nur mit  , wie in:

 

---

Wenn Ihre Anwendung (irgendwie) nicht mit etwas anderem kommunizieren und auf dessen Antwort warten muss, verwenden Sie  , auch wenn Sie   im Inneren nicht verwenden müssen.

---

Wenn Sie sich unsicher sind, verwenden Sie normales  .

---

**Hinweis**: Sie können   und   in Ihren *Pfadoperation-Funktionen* beliebig mischen, so wie Sie es benötigen, und jede einzelne Funktion in der für Sie besten Variante erstellen. FastAPI wird damit das Richtige tun.

Wie dem auch sei, in jedem der oben genannten Fälle wird FastAPI immer noch asynchron arbeiten und extrem schnell sein.

Wenn Sie jedoch den oben genannten Schritten folgen, können einige Performanz-Optimierungen vorgenommen werden.

## Technische Details  

Moderne Versionen von Python unterstützen **„asynchronen Code“** unter Verwendung sogenannter **„Coroutinen“** mithilfe der Syntax **  und  **.

Nehmen wir obigen Satz in den folgenden Abschnitten Schritt für Schritt unter die Lupe:

* **Asynchroner Code**
* **  und  **
* **Coroutinen**

## Asynchroner Code  

Asynchroner Code bedeutet lediglich, dass die Sprache 💬 eine Möglichkeit hat, dem Computer / Programm 🤖 mitzuteilen, dass es 🤖 an einem bestimmten Punkt im Code darauf warten muss, dass *etwas anderes* irgendwo anders fertig wird. Nehmen wir an, *etwas anderes* ist hier „Langsam-Datei“ 📝.

Während der Zeit, die „Langsam-Datei“ 📝 benötigt, kann das System also andere Aufgaben erledigen.

Dann kommt der Computer / das Programm 🤖 bei jeder Gelegenheit zurück, weil es entweder wieder wartet oder wann immer es 🤖 die ganze Arbeit erledigt hat, die zu diesem Zeitpunkt zu tun war. Und es 🤖 wird nachschauen, ob eine der Aufgaben, auf die es gewartet hat, bereits fertig ist, und tun, was es zu tun hatte.

Dann nimmt es 🤖 die erste erledigte Aufgabe (sagen wir, unsere „Langsam-Datei“ 📝) und bearbeitet sie weiter.

