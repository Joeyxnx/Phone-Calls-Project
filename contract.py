import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class MTMContract(Contract):
    """ A Month-to-Month contract for a phone number

    === Public Attributes ===
    start:
        beginning date for the MTM contract
    finish:
        last date for the MTM contract
    bill:
       bill for this contract for the last month of call records loaded from
        the input dataset
    """

    start: datetime.datetime
    finish: datetime.datetime
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Implement a new MTM contract with the attribute
            <start> date, begins as inactive
        """

        Contract.__init__(self, start)
        self.finish = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        bill.set_rates("MTM", MTM_MINS_COST)
        bill.add_fixed_cost(MTM_MONTHLY_FEE)
        self.bill = bill


class TermContract(Contract):
    """ A Term contract for a phone line

    === Public Attributes ===
    start:
        starting date for the contract
    finish:
        ending date for the contract
    bill:
        bill for this contract for the last month of call records loaded
         the input dataset
    freebie:
        free minutes for a phone line
    point:
        current date of TermContract
    """

    start: datetime.datetime
    finish: datetime.datetime
    bill: Optional[Bill]
    freebies: int
    point: datetime.datetime

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new TermContract with the <start> date,
            starts as inactive
        """

        Contract.__init__(self, start)
        self.finish = end
        self.freebies = TERM_MINS
        self.point = start

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """

        bill.set_rates("TERM", TERM_MINS_COST)
        bill.add_fixed_cost(TERM_MONTHLY_FEE)
        if month == self.start.month:
            if year == self.start.year:
                bill.add_fixed_cost(TERM_DEPOSIT)
        self.point = datetime.date(year, month, 1)
        self.bill = bill

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """

        mn = ceil(call.duration / 60.0)
        if 0 < self.freebies < mn:
            self.freebies = 0
            self.bill.add_free_minutes(self.freebies)
            self.bill.add_billed_minutes(mn - self.freebies)

        elif self.freebies >= mn:
            self.freebies -= mn
            self.bill.add_free_minutes(mn)

        else:
            self.bill.add_billed_minutes(mn)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
                with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        if self.point <= self.finish:
            return self.bill.get_cost()
        else:
            return self.bill.get_cost() - TERM_DEPOSIT


class PrepaidContract(Contract):
    """ A Prepaid contract for a phone line

        === Public Attributes ===
    start:
        beginning date for the MTM contract
    finish:
        last date for the MTM contract
    bill:
        bill for this contract for the last month of call records loaded from
        the input dataset
    bal:
        The balance for this account, negative is credit
    """
    start: datetime.datetime
    finish: datetime.datetime
    bill: Optional[Bill]
    bal: int

    def __init__(self, start: datetime.date, balance: float) -> None:
        """ Create a new PrepaidContract with the <start> date,
            starts as inactive
        """

        Contract.__init__(self, start)
        self.bal = -balance
        self.finish = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        bill.set_rates("PREPAID", PREPAID_MINS_COST)
        try:
            self.bal = self.bill.get_cost()
        except AttributeError:
            pass
        while not self.bal <= -10:
            self.bal -= 25
        bill.add_fixed_cost(self.bal)
        self.bill = bill

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
            with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancellation is requested.
        """
        self.start = None
        if self.bill.get_cost() <= 0:
            return 0
        else:
            return self.bill.get_cost()


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
