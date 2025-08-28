"""
Family Office Services Module

Comprehensive family office wealth management services including:
- Multi-generational wealth planning
- Trust structure optimization
- Estate planning with tax considerations
- Business succession planning
- Philanthropic strategy development
- Education funding planning
- Tax optimization across generations
"""

from .wealth_management import (
    FamilyOfficeManager,
    TrustType,
    BusinessStructure,
    PhilanthropicVehicle,
    FamilyMember,
    TrustStructure,
    BusinessEntity,
    EducationPlan,
    PhilanthropicStrategy
)

__all__ = [
    'FamilyOfficeManager',
    'TrustType',
    'BusinessStructure', 
    'PhilanthropicVehicle',
    'FamilyMember',
    'TrustStructure',
    'BusinessEntity',
    'EducationPlan',
    'PhilanthropicStrategy'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Family Office Development Team'
__description__ = 'Comprehensive family office wealth management system'