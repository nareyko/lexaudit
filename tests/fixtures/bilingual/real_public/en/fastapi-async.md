# Concurrency and async / await  

Details about the   syntax for *path operation functions* and some background about asynchronous code, concurrency, and parallelism.

## In a hurry?  

  TL;DR:  

If you are using third party libraries that tell you to call them with  , like:

 

Then, declare your *path operation functions* with   like:

 

 

You can only use   inside of functions created with  .

 
---

If you are using a third party library that communicates with something (a database, an API, the file system, etc.) and doesn't have support for using  , (this is currently the case for most database libraries), then declare your *path operation functions* as normally, with just  , like:

 

---

If your application (somehow) doesn't have to communicate with anything else and wait for it to respond, use  , even if you don't need to use   inside.

---

If you just don't know, use normal  .

---

**Note**: You can mix   and   in your *path operation functions* as much as you need and define each one using the best option for you. FastAPI will do the right thing with them.

Anyway, in any of the cases above, FastAPI will still work asynchronously and be extremely fast.

But by following the steps above, it will be able to do some performance optimizations.

## Technical Details  

Modern versions of Python have support for **"asynchronous code"** using something called **"coroutines"**, with **  and  ** syntax.

Let's see that phrase by parts in the sections below:

* **Asynchronous Code**
* **  and  **
* **Coroutines**

## Asynchronous Code  

Asynchronous code just means that the language 💬 has a way to tell the computer / program 🤖 that at some point in the code, it 🤖 will have to wait for *something else* to finish somewhere else. Let's say that *something else* is called "slow-file" 📝.

So, during that time, the computer can go and do some other work, while "slow-file" 📝 finishes.

Then the computer / program 🤖 will come back every time it has a chance because it's waiting again, or whenever it 🤖 finishes all the work it had at that point. And it 🤖 will see if any of the tasks it was waiting for have already finished, doing whatever it had to do.

Next, it 🤖 takes the first task to finish (let's say, our "slow-file" 📝) and continues whatever it had to do with it.

That "wait for something else" normally refers to  I/O  operations that are relatively "slow" (compared to the speed of the processor and the RAM memory), like waiting for:

