# Path Parameters  

You can declare path "parameters" or "variables" with the same syntax used by Python format strings:

 

The value of the path parameter   will be passed to your function as the argument  .

So, if you run this example and go to   you will see a response of:

 

## Path parameters with types  

You can declare the type of a path parameter in the function, using standard Python type annotations:

 

In this case,   is declared to be an  .

 

This will give you editor support inside of your function, with error checks, completion, etc.

 
## Data  conversion   

If you run this example and open your browser at   you will see a response of:

 

 

Notice that the value your function received (and returned) is  , as a Python  , not a string  .

So, with that type declaration, **FastAPI** gives you automatic request  "parsing" .

 
## Data validation  

But if you go to the browser at   you will see a nice HTTP error of:

 

because the path parameter   had a value of  , which is not an  .

The same error would appear if you provided a   instead of an  , as in:  

 

So, with the same Python type declaration, **FastAPI** gives you data validation.

Notice that the error also clearly states exactly the point where the validation didn't pass.

This is incredibly helpful while developing and debugging code that interacts with your API.

 
## Documentation  

And when you open your browser at   you will see an automatic, interactive, API documentation like:

 

 

Again, just with that same Python type declaration, **FastAPI** gives you automatic, interactive documentation (integrating Swagger UI).

Notice that the path parameter is declared to be an integer.

 
## Standards-based benefits, alternative documentation  

And because the generated schema is from the OpenAPI standard, there are many compatible tools.

Because of this, **FastAPI** itself provides an alternative API documentation (using ReDoc), which you can access at  

 

The same way, there are many compatible tools. Including code generation tools for many languages.

## Pydantic  

All the data validation is performed under the hood by Pydantic, so you get all the benefits from it. And you know you are in good hands.

You can use the same type declarations with  ,  ,   and many other complex data types.

Several of these are explored in the next chapters of the tutorial.

## Order matters  

When creating *path operations*, you can find situations where you have a fixed path.

Like  , let's say that it's to get data about the current user.

And then you can also have a path   to get data about a specific user by some user ID.

Because *path operations* are evaluated in order, you need to make sure that the path for   is declared before the one for  :

