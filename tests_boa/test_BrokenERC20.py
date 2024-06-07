import os
import pytest
import boa
from decimal import Decimal

@pytest.fixture
def deployer():
    acc = boa.env.generate_address(alias="deployer")
    boa.env.set_balance(acc, 1000*10**18)
    return acc

@pytest.fixture
def trader():
    acc = boa.env.generate_address(alias="trader")
    boa.env.set_balance(acc, 1000*10**18)
    return acc

@pytest.fixture
def broke_erc20(deployer, trader):
    with boa.env.prank(deployer):
        b20 = boa.load("contracts/test_helpers/BrokenERC20.vy", "BrokenERC20", "BAD", 18, 1000*10**18, deployer)
        b20.mint(trader, 100000)
    return b20

@pytest.fixture
def erc20(deployer, trader):
    with boa.env.prank(deployer):
        erc = boa.load("contracts/test_helpers/ERC20.vy", "ERC20", "Coin", 18, 1000*10**18, deployer)
    return erc    

@pytest.fixture
def gov(deployer):
    with boa.env.prank(deployer):
        g = boa.load("contracts/Governance.vy", deployer, 21600)
    return g

@pytest.fixture
def funds_alloc(deployer):
    with boa.env.prank(deployer):
        f = boa.load("contracts/FundsAllocator.vy")
    return f

@pytest.fixture
def adapter(deployer, broke_erc20, erc20):
    with boa.env.prank(deployer):
        a = boa.load("contracts/adapters/MockLPAdapter.vy", broke_erc20, erc20)
    return a

@pytest.fixture
def vault(deployer, broke_erc20, funds_alloc, gov, adapter):
    with boa.env.prank(deployer):
        v = boa.load(
            "contracts/AdapterVault.vy",
            "TestVault",
            "vault",
            18,
            broke_erc20,
            [adapter,],
            gov,
            funds_alloc,
            Decimal(2.0)
        )
    return v

def test_vault(vault, deployer, trader, broke_erc20):

    with boa.env.prank(trader):
        broke_erc20.approve(vault.address, broke_erc20.balanceOf(trader))

        vault.deposit(10000, trader)

        assert vault.balanceOf(trader) == 10000

