from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class AddressAssociation(db.Model):
    __tablename__ = "address_association"
    id = db.Column(db.Integer, primary_key=True)
    discriminator = db.Column(db.String)
    __mapper_args__ = {"polymorphic_on": discriminator}


class Address(db.Model):
    __tablename__ = "address"
    id = db.Column(db.Integer, primary_key=True)
    association_id = db.Column(db.Integer, db.ForeignKey("address_association.id"))
    street = db.Column(db.String)
    city = db.Column(db.String)
    zip = db.Column(db.String)
    association = db.relationship("AddressAssociation", backref="addresses")

    parent = association_proxy("association", "parent")

    def __repr__(self):
        return "%s(street=%r, city=%r, zip=%r)" % \
               (self.__class__.__name__, self.street,
                self.city, self.zip)


class HasAddresses(object):
    @declared_attr
    def address_association_id(cls):
        return db.Column(db.Integer, db.ForeignKey("address_association.id"))

    @declared_attr
    def address_association(cls):
        name = cls.__name__
        discriminator = name.lower()

        assoc_cls = type(
            "%sAddressAssociation" % name,
            (AddressAssociation,),
            dict(
                __mapper_args__={
                    "polymorphic_identity": discriminator
                }
            )
        )

        cls.addresses = association_proxy(
            "address_association", "addresses",
            creator=lambda addresses: assoc_cls(addresses=addresses)
        )
        return db.relationship(assoc_cls,
                               backref=db.backref("parent", uselist=False))


class Customer(HasAddresses, db.Model):
    __tablename__ = "customer"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class Supplier(HasAddresses, db.Model):
    __tablename__ = "supplier"
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String)


db.create_all()


def test():
    session = db.session

    session.add_all([
        Customer(
            name='customer 1',
            addresses=[
                Address(
                    street='123 anywhere street',
                    city="New York",
                    zip="10110"),
                Address(
                    street='40 main street',
                    city="San Francisco",
                    zip="95732")
            ]
        ),
        Supplier(
            company_name="Ace Hammers",
            addresses=[
                Address(
                    street='2569 west elm',
                    city="Detroit",
                    zip="56785")
            ]
        ),
    ])

    session.commit()

    for customer in session.query(Customer):
        for address in customer.addresses:
            print(address)
            print(address.parent)


@app.route('/')
def hello_world():
    test()
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
