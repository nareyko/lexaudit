# First Steps  

The simplest FastAPI file could look like this:

 

Copy that to a file  .

 

FastAPI has an official extension for VS Code (and Cursor), which provides a lot of features, including a path operation explorer, path operation search, CodeLens navigation in tests (jump to definition from tests), and FastAPI Cloud deployment and logs, all from your editor.

 

 

 

 

In the output, there's a line with something like:

 

That line shows the URL where your app is being served on your local machine.

### Check it  

Open your browser at  

You will see the JSON response as:

 

### Interactive API docs  

Now go to  

You will see the automatic interactive API documentation (provided by Swagger UI):

 

### Alternative API docs  

And now, go to  

You will see the alternative automatic documentation (provided by ReDoc):

 

### OpenAPI  

**FastAPI** generates a "schema" with all your API using the **OpenAPI** standard for defining APIs.

#### "Schema"  

A "schema" is a definition or description of something. Not the code that implements it, but just an abstract description.

#### API "schema"  

In this case, OpenAPI is a specification that dictates how to define a schema of your API.

This schema definition includes your API paths, the possible parameters they take, etc.

#### Data "schema"  

The term "schema" might also refer to the shape of some data, like a JSON content.

In that case, it would mean the JSON attributes, and data types they have, etc.

#### OpenAPI and JSON Schema  

OpenAPI defines an API schema for your API. And that schema includes definitions (or "schemas") of the data sent and received by your API using **JSON Schema**, the standard for JSON data schemas.

#### Check the    

If you are curious about what the raw OpenAPI schema looks like, FastAPI automatically generates a JSON (schema) with the descriptions of all your API.

You can see it directly at:  

It will show a JSON starting with something like:

 

#### What is OpenAPI for  

The OpenAPI schema is what powers the two interactive documentation systems included.

And there are dozens of alternatives, all based on OpenAPI. You could easily add any of those alternatives to your application built with **FastAPI**.

You could also use it to generate code automatically, for clients that communicate with your API. For example, frontend, mobile or IoT applications.

### Configure the app   in    

You can configure where your app is located in a   file like:

 

That   will tell the   command that it should import the app like:

 

If your code was structured like:

 

Then you would set the   as:

 

which would be equivalent to:

 

###   with path or with   CLI option

