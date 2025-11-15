# sample CURL Requests


### create new user

    curl -X POST http://localhost:8000/users -H "Content-Type: application/json" \
    -d '{"email":"alice@example.com","delivery_address":"123 Maple St"}'

### create new order for user

    curl -X POST http://localhost:8003/orders -H "Content-Type: application/json" \
      -d '{"items":["item1","item2"],"email":"alice@example.com","delivery_address":"123 Maple St", "user_id": "1"}'


### update user fields

    curl -X PUT http://localhost:8000/users/1 -H "Content-Type: application/json" \
    -d '{"email":"a2@example.com"}'

    curl -X PUT http://localhost:8000/users/1 -H "Content-Type: application/json" \
    -d '{"delivery_address": "12345 main st"}'