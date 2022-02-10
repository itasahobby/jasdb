# Just a Simple DB

This project showcases a simple database with a custom application layer protocol.

 ```
  0              
 0 1 2 3 4 5 6 7
+-+-+-+-+-+-+-+-+
|Me.|     ID    |
+-+-+-+-+-+-+-+-+
|      Auth     |
+-+-+-+-+-+-+-+-+
 ```

> Header specification followed by up to 510 bytes of data.

The protocol supports four methods inspired from HTTP:
* GET: Gets the data in a specific index
* POST: Push data to the next free slot if any
* UPDATE: Push data to a specific index slot
* DELETE: Erases data from an index