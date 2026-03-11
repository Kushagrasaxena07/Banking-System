import uuid
import os
import json   

class Account:
    def __init__(self, account_number, owner_id, initial_balance=0.0):
        self.account_number = account_number
        self.owner_id = owner_id
        self.balance = initial_balance

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            return True
        return False

    def withdraw(self, amount):
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            return True
        return False

    def to_dict(self):
        return {
            "account_number": self.account_number,
            "owner_id": self.owner_id,
            "balance": self.balance
        }

    def display(self):
        return f"Account No: {self.account_number}, Balance: ₹{self.balance:.2f}"


class SavingsAccount(Account):
    def __init__(self, account_number, owner_id, initial_balance=0.0, interest_rate=0.01):
        super().__init__(account_number, owner_id, initial_balance)
        self.interest_rate = interest_rate

    def apply_interest(self):
        interest = self.balance * self.interest_rate
        self.balance += interest

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "savings"
        data["interest_rate"] = self.interest_rate
        return data

    def display(self):
        base = super().display()
        return f"{base}, Interest Rate: {self.interest_rate * 100:.2f}%"


class CheckingAccount(Account):
    def __init__(self, account_number, owner_id, initial_balance=0.0, overdraft_limit=0.0):
        super().__init__(account_number, owner_id, initial_balance)
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount):
        if amount > 0 and (self.balance + self.overdraft_limit) >= amount:
            self.balance -= amount
            return True
        return False

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "checking"
        data["overdraft_limit"] = self.overdraft_limit
        return data

    def display(self):
        base = super().display()
        return f"{base}, Overdraft Limit: ₹{self.overdraft_limit:.2f}"


class Customer:
    def __init__(self, customer_id, name, address):
        self.customer_id = customer_id
        self.name = name
        self.address = address
        self.account_numbers = []

    def add_account(self, account_number):
        self.account_numbers.append(account_number)

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "address": self.address,
            "account_numbers": self.account_numbers
        }

    def display(self):
        return f"ID: {self.customer_id}, Name: {self.name}, Address: {self.address}, Accounts: {len(self.account_numbers)}"


class Bank:
    def __init__(self, customer_file='customers.json', account_file='accounts.json'):
        self.customers = {}
        self.accounts = {}
        self.customer_file = customer_file
        self.account_file = account_file
        self.load_data()

    def load_data(self):
        if os.path.exists(self.customer_file):
            with open(self.customer_file, 'r') as f:
                for cust in json.load(f):
                    customer = Customer(cust['customer_id'], cust['name'], cust['address'])
                    customer.account_numbers = cust.get('account_numbers', [])
                    self.customers[cust['customer_id']] = customer

        if os.path.exists(self.account_file):
            with open(self.account_file, 'r') as f:
                for acc in json.load(f):
                    if acc.get('type') == 'savings':
                        account = SavingsAccount(acc['account_number'], acc['owner_id'], acc['balance'], acc.get('interest_rate',0.01))
                    elif acc.get('type') == 'checking':
                        account = CheckingAccount(acc['account_number'], acc['owner_id'], acc['balance'], acc.get('overdraft_limit',0.0))
                    else:
                        account = Account(acc['account_number'], acc['owner_id'], acc['balance'])

                    self.accounts[acc['account_number']] = account

    def save_data(self):
        with open(self.customer_file, 'w') as f:
            json.dump([c.to_dict() for c in self.customers.values()], f, indent=4)

        with open(self.account_file, 'w') as f:
            json.dump([a.to_dict() for a in self.accounts.values()], f, indent=4)

    def add_customer(self, customer):
        if customer.customer_id in self.customers:
            return False

        self.customers[customer.customer_id] = customer
        self.save_data()
        return True

    def create_account(self, customer_id, account_type, initial_balance=0.0, **kwargs):
        if customer_id not in self.customers:
            return None

        acc_num = str(uuid.uuid4())

        if account_type == "savings":
            account = SavingsAccount(acc_num, customer_id, initial_balance, kwargs.get("interest_rate",0.01))
        elif account_type == "checking":
            account = CheckingAccount(acc_num, customer_id, initial_balance, kwargs.get("overdraft_limit",0.0))
        else:
            return None

        self.accounts[acc_num] = account
        self.customers[customer_id].add_account(acc_num)
        self.save_data()

        return account

    def deposit(self, acc_num, amount):
        account = self.accounts.get(acc_num)

        if account and account.deposit(amount):
            self.save_data()
            return True

        return False

    def withdraw(self, acc_num, amount):
        account = self.accounts.get(acc_num)

        if account and account.withdraw(amount):
            self.save_data()
            return True

        return False

    def apply_interest_all(self):
        for acc in self.accounts.values():
            if isinstance(acc, SavingsAccount):
                acc.apply_interest()

        self.save_data()

    def show_customers(self):
        for c in self.customers.values():
            print(c.display())

    def show_accounts(self):
        for a in self.accounts.values():
            print(a.display())


def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except:
            print("Invalid number")


def main():

    bank = Bank()

    while True:

        print("""
1 Add Customer
2 Create Account
3 Deposit
4 Withdraw
5 Apply Interest
6 Show Customers
7 Show Accounts
8 Exit
""")

        choice = input("Enter choice: ")

        if choice == "1":

            cid = input("Customer ID: ")
            name = input("Name: ")
            addr = input("Address: ")

            c = Customer(cid,name,addr)

            if bank.add_customer(c):
                print("Customer Added")

        elif choice == "2":

            cid = input("Customer ID: ")
            typ = input("Type (savings/checking): ")

            balance = input_float("Initial deposit: ")

            kwargs = {}

            if typ == "savings":
                kwargs["interest_rate"] = input_float("Interest rate: ")

            if typ == "checking":
                kwargs["overdraft_limit"] = input_float("Overdraft limit: ")

            acc = bank.create_account(cid,typ,balance,**kwargs)

            if acc:
                print("Account created:",acc.account_number)

        elif choice == "3":

            acc = input("Account number: ")
            amt = input_float("Amount: ")

            if bank.deposit(acc,amt):
                print("Deposit successful")

        elif choice == "4":

            acc = input("Account number: ")
            amt = input_float("Amount: ")

            if bank.withdraw(acc,amt):
                print("Withdraw successful")

        elif choice == "5":

            bank.apply_interest_all()
            print("Interest applied")

        elif choice == "6":

            bank.show_customers()

        elif choice == "7":

            bank.show_accounts()

        elif choice == "8":

            print("Goodbye")
            break


if __name__ == "__main__":
    main()
