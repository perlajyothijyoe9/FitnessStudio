from fitness import fitness
from fitness.controller import (
    all,
    admin,
    bookings,
    classes,
    membership,
    payment,
    trainer,
    user,
)

if __name__ == "__main__":
    fitness.run(host="0.0.0.0", port=5000, debug=True)
