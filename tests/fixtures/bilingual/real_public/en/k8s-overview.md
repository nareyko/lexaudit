This page is an overview of Kubernetes.

 

The name Kubernetes originates from Greek, meaning helmsman or pilot. K8s as an abbreviation
results from counting the eight letters between the "K" and the "s". Google open sourced the
Kubernetes project in 2014. Kubernetes combines
over 15 years of Google's experience running
production workloads at scale with best-of-breed ideas and practices from the community.

## Why you need Kubernetes and what it can do {#why-you-need-kubernetes-and-what-can-it-do}

Containers are a good way to bundle and run your applications. In a production
environment, you need to manage the containers that run the applications and
ensure that there is no downtime. For example, if a container goes down, another
container needs to start. Wouldn't it be easier if this behavior was handled by a system?

That's how Kubernetes comes to the rescue! Kubernetes provides you with a framework
to run distributed systems resiliently. It takes care of scaling and failover for
your application, provides deployment patterns, and more. For example: Kubernetes
can easily manage a canary deployment for your system.

Kubernetes provides you with:

