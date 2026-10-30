_Pods_ sind die kleinsten einsetzbaren Einheiten, die in Kubernetes
erstellt und verwaltet werden können.

Ein _Pod_ (übersetzt Gruppe/Schote, wie z. B. eine Gruppe von Walen oder eine 
Erbsenschote) ist eine Gruppe von einem oder mehreren 
{{ }} mit gemeinsam 
genutzten Speicher- und Netzwerkressourcen und einer Spezifikation für die 
Ausführung der Container. Die Ressourcen eines Pods befinden sich immer auf dem 
gleichen (virtuellen) Server, werden gemeinsam geplant und in einem
gemeinsamen Kontext ausgeführt. Ein Pod modelliert einen anwendungsspezifischen 
"logischen Server": Er enthält eine oder mehrere containerisierte Anwendungen, 
die relativ stark voneinander abhängen. 
In Nicht-Cloud-Kontexten sind Anwendungen, die auf
demselben physischen oder virtuellen Server ausgeführt werden, vergleichbar zu 
Cloud-Anwendungen, die auf demselben logischen Server ausgeführt werden.

Ein Pod kann neben Anwendungs-Containern auch sogenannte 
Initialisierungs-Container
enthalten, die beim Starten des Pods ausgeführt werden.
Es können auch 
kurzlebige/ephemere Container
zum Debuggen gestartet werden, wenn dies der Cluster anbietet.

 

## Was ist ein Pod?

{{ }}
Obwohl Kubernetes abgesehen von Docker auch andere
{{ }} unterstützt, ist Docker am bekanntesten und
 es ist hilfreich, Pods mit der Terminologie von Docker zu beschreiben.
{{ }}

Der gemeinsame Kontext eines Pods besteht aus einer Reihe von Linux-Namespaces, 
Cgroups und möglicherweise anderen Aspekten der Isolation, also die gleichen
Dinge, die einen Dockercontainer isolieren. Innerhalb des Kontexts eines Pods 
können die einzelnen Anwendungen weitere Unterisolierungen haben. 

Im Sinne von Docker-Konzepten ähnelt ein Pod einer Gruppe von Docker-Containern, 
die gemeinsame Namespaces und Dateisystem-Volumes nutzen.

## Pods verwenden

Normalerweise müssen keine Pods erzeugt werden, auch keine Singleton-Pods. 
Stattdessen werden sie mit Workload-Ressourcen wie {{ }} oder {{ }} erzeugt. Für Pods, die von einem Systemzustand
abhängen, ist die Nutzung von {{ }}-Ressourcen zu erwägen.

Pods in einem Kubernetes-Cluster werden hauptsächlich auf zwei Arten verwendet:

