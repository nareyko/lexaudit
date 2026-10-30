# Features  

## FastAPI features  

**FastAPI** gives you the following:

### Based on open standards  

* **OpenAPI** for API creation, including declarations of  path   operations , parameters, request bodies, security, etc.
* Automatic data model documentation with **JSON Schema** (as OpenAPI itself is based on JSON Schema).
* Designed around these standards, after a meticulous study. Instead of an afterthought layer on top.
* This also allows using automatic **client code generation** in many languages.

### Automatic docs  

Interactive API documentation and exploration web user interfaces. As the framework is based on OpenAPI, there are multiple options, 2 included by default.

* **Swagger UI**, with interactive exploration, call and test your API directly from the browser.

 

* Alternative API documentation with **ReDoc**.

 

### Just Modern Python  

It's all based on standard **Python type** declarations (thanks to Pydantic). No new syntax to learn. Just standard modern Python.

If you need a 2 minute refresher of how to use Python types (even if you don't use FastAPI), check the short tutorial: Python Types.

You write standard Python with types:

 

That can then be used like:

 

 

  means:

Pass the keys and values of the   dict directly as key-value arguments, equivalent to:  

 
### Editor support  

The whole framework was designed to be easy and intuitive to use, all the decisions were tested on multiple editors even before starting development, to ensure the best development experience.

In the Python developer surveys, it's clear that one of the most used features is "autocompletion".

The whole **FastAPI** framework is designed to satisfy that. Autocompletion works everywhere.

You will rarely need to come back to the docs.

Here's how your editor might help you:

* in Visual Studio Code:

 

* in PyCharm:

 

You will get completion in code you might even consider impossible before. As for example, the   key inside a JSON body (that could have been nested) that comes from a request.

No more typing the wrong key names, coming back and forth between docs, or scrolling up and down to find if you finally used   or  .

### Short  

It has sensible **defaults** for everything, with optional configurations everywhere. All the parameters can be fine-tuned to do what you need and to define the API you need.

But by default, it all **"just works"**.

### Validation  

* Validation for most (or all?) Python **data types**, including:
    * JSON objects ( ).
    * JSON array ( ) defining item types.
    * String ( ) fields, defining min and max lengths.
    * Numbers ( ,  ) with min and max values, etc.

* Validation for more exotic types, like:
    * URL.
    * Email.
    * UUID.
    * ...and others.

