# Query Parameters  

When you declare other function parameters that are not part of the path parameters, they are automatically interpreted as "query" parameters.

 

The query is the set of key-value pairs that go after the   in a URL, separated by   characters.

For example, in the URL:

 

...the query parameters are:

*  : with a value of  
*  : with a value of  

As they are part of the URL, they are "naturally" strings.

But when you declare them with Python types (in the example above, as  ), they are converted to that type and validated against it.

All the same processes that apply to path parameters also apply to query parameters:

* Editor support (obviously)
* Data  "parsing" 
* Data validation
* Automatic documentation

## Defaults  

As query parameters are not a fixed part of a path, they can be optional and can have default values.

In the example above they have default values of   and  .

So, going to the URL:

 

would be the same as going to:

 

But if you go to, for example:

 

The parameter values in your function will be:

*  : because you set it in the URL
*  : because that was the default value

## Optional parameters  

The same way, you can declare optional query parameters, by setting their default to  :

 

In this case, the function parameter   will be optional, and will be   by default.

 

Also notice that **FastAPI** is smart enough to notice that the path parameter   is a path parameter and   is not, so, it's a query parameter.

 
## Query parameter type conversion  

You can also declare   types, and they will be converted:

 

In this case, if you go to:

 

or

 

or

 

or

 

or

 

or any other case variation (uppercase, first letter in uppercase, etc), your function will see the parameter   with a   value of  .

Values such as  ,  ,  , and   (including case variations) are converted to  .

If   is omitted, **FastAPI** uses its default value, which is   in this example.

An empty value ( ) or an unrecognized value (for example,  ) produces a   validation error.

## Multiple path and query parameters  

You can declare multiple path parameters and query parameters at the same time, **FastAPI** knows which is which.

And you don't have to declare them in any specific order.

They will be detected by name:

 

## Required query parameters  

When you declare a default value for non-path parameters (for now, we have only seen query parameters), then it is not required.

If you don't want to add a specific value but just make it optional, set the default as  .

But when you want to make a query parameter required, you can just not declare any default value:

 

Here the query parameter   is a required query parameter of type  .

If you open in your browser a URL like:

