Ok now add this models.


Product:
- title: max char 100
- quantity: positive int
- unit: (gram, pice)
- price: simple (+) int no complex system like update over time


Due:
- product
- date
- is_edited
- amount: amount may not = all product price is not necessary cuz user give some discount and charge less from a customer.
- customer


Deposit:
- amount
- date


Customer:
- name: max char 30
- phone_number (optional)
- address (optional)
    methods:
    - total_due_amount


one User can have many Customers.
one Customer can have many Due(s) and Deposit(s)
one Due can have many Product(s)

Note:
Its not necessary to have duplicates product. same name same price can have many products.

project overview:
a due management system for a shopkeeper. who trace all there customers dues there deposit. this system is not for Customers.


just add those Models. and unit test for those models. no serializer not require for this prompt.