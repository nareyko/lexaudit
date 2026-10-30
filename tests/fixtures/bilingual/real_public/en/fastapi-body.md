# Request Body  

When you need to send data from a client (let's say, a browser) to your API, you send it as a **request body**.

A **request** body is data sent by the client to your API. A **response** body is the data your API sends to the client.

Your API almost always has to send a **response** body. But clients don't necessarily need to send **request bodies** all the time, sometimes they only request a path, maybe with some query parameters, but don't send a body.

To declare a **request** body, you use Pydantic models with all their power and benefits.

 

To send data, you should use one of:   (the most common),  ,   or  .

Sending a body with a   request has an undefined behavior in the specifications, nevertheless, it is supported by FastAPI, only for very complex/extreme use cases.

As it is discouraged, the interactive docs with Swagger UI won't show the documentation for the body when using  , and proxies in the middle might not support it.

 
## Import Pydantic's    

First, you need to import   from  :

 

## Create your data model  

Then you declare your data model as a class that inherits from  .

Use standard Python types for all the attributes:

 

The same as when declaring query parameters, when a model attribute has a default value, it is not required. Otherwise, it is required. Use   to make it just optional.

For example, this model above declares a JSON " " (or Python  ) like:

 

...as   and   are optional (with a default value of  ), this JSON " " would also be valid:

 

## Declare it as a parameter  

To add it to your *path operation*, declare it the same way you declared path and query parameters:

 

...and declare its type as the model you created,  .

## Results  

With just that Python type declaration, **FastAPI** will:

* Read the body of the request as JSON.
* Convert the corresponding types (if needed).
* Validate the data.
    * If the data is invalid, it will return a nice and clear error, indicating exactly where and what was the incorrect data.
* Give you the received data in the parameter  .
    * As you declared it in the function to be of type  , you will also have all the editor support (completion, etc) for all of the attributes and their types.
* Generate JSON Schema definitions for your model, you can also use them anywhere else you like if it makes sense for your project.
* Those schemas will be part of the generated OpenAPI schema, and used by the automatic documentation  UIs .

## Automatic docs  

The JSON Schemas of your models will be part of your OpenAPI generated schema, and will be shown in the interactive API docs:

 

And will also be used in the API docs inside each *path operation* that needs them:

 

## Editor support

