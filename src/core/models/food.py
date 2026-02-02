from sqlalchemy import Column, String, Integer, Numeric, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FoodBalance(Base):
    """
    SQLAlchemy model for food_balance table
    Represents food balance data with composite primary key (food_label, years, unit)
    """
    __tablename__ = 'food_balance'
    
    food_label = Column(String, nullable=False, comment="Food category label")
    years = Column(Integer, nullable=False, comment="Year of the data")
    unit = Column(String, nullable=False, comment="Unit of measurement")
    amount = Column(Numeric, nullable=True, comment="Amount value (can be NULL/NA)")
    
    # Define composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('food_label', 'years', 'unit', name='food_balance_pk'),
    )
    
    def __repr__(self):
        return f"<FoodBalance(food_label='{self.food_label}', years={self.years}, unit='{self.unit}', amount={self.amount})>"
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'food_label': self.food_label,
            'years': self.years,
            'unit': self.unit,
            'amount': float(self.amount) if self.amount is not None else None
        }


class HouseholdSpending(Base):
    """
    SQLAlchemy model for household_spending table
    Represents household spending data with composite primary key (food_code, years)
    """
    __tablename__ = 'household_spending'
    
    food_code = Column(String, nullable=False, comment="Food category code")
    units = Column(String, nullable=True, comment="Unit of measurement (can be NULL/NA)")
    years = Column(Integer, nullable=False, comment="Year of the data")
    amount = Column(Numeric, nullable=True, comment="Spending amount (can be NULL/NA)")
    rse_indicator = Column(String, nullable=True, comment="RSE indicator (can be NULL/NA)")
    
    # Define composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('food_code', 'years', name='household_spending_pk'),
    )
    
    def __repr__(self):
        return f"<HouseholdSpending(food_code='{self.food_code}', years={self.years}, amount={self.amount})>"
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'food_code': self.food_code,
            'units': self.units,
            'years': self.years,
            'amount': float(self.amount) if self.amount is not None else None,
            'rse_indicator': self.rse_indicator
        }