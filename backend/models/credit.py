class Credit:
    def __init__(self, amount, interest_rate):
        self.amount = amount
        self.interest_rate = interest_rate

    def calculate_monthly_payment(self, years):
        monthly_rate = self.interest_rate / 12 / 100
        number_of_payments = years * 12
        if monthly_rate == 0:
            return self.amount / number_of_payments
        else:
            return (self.amount * monthly_rate) / (1 - (1 + monthly_rate) ** -number_of_payments)

    def total_payment(self, years):
        return self.calculate_monthly_payment(years) * years * 12

    def total_interest(self, years):
        return self.total_payment(years) - self.amount