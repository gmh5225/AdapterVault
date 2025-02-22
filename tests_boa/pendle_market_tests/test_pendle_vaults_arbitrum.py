from ..conftest import forked_env_arbitrum
import os
import pytest
import boa
import json
from boa.environment import Env
from web3 import Web3
import eth_abi
from decimal import Decimal

PENDLE_ROUTER="0x00000000005BBB0EF59571E58418F9a4357b68A0"
PENDLE_ROUTER_STATIC="0xAdB09F65bd90d19e3148D9ccb693F3161C6DB3E8"
PENDLE_ORACLE="0x1Fd95db7B7C0067De8D45C0cb35D59796adfD187"

MAX_UINT256 = 115792089237316195423570985008687907853269984665640564039457584007913129639935
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
MAX_ADAPTERS = 5 # Must match the value from AdapterVault.vy

@pytest.fixture
def setup_chain():
    with boa.swap_env(Env()):
        #tests in this file require arbitrum block 211000000: May-14-2024 12:08:32 AM +UTC
        forked_env_arbitrum(211000000)
        yield

@pytest.fixture
def vault_blueprint(setup_chain):
    f = boa.load_partial("contracts/AdapterVault.vy")
    return f.deploy_as_blueprint()

def access_vault(addr):
    f = boa.load_partial("contracts/AdapterVault.vy")
    return f.at(addr)

def access_adapter(addr):
    f = boa.load_partial("contracts/adapters/PendleAdapter.vy")
    return f.at(addr)

@pytest.fixture
def pendle_adapter_blueprint(setup_chain):
    f = boa.load_partial("contracts/adapters/PendleAdapter.vy")
    return f.deploy_as_blueprint()

@pytest.fixture
def pendle_factory(setup_chain, deployer, funds_alloc, vault_blueprint, pendle_adapter_blueprint):
    with boa.env.prank(deployer):
        pa = boa.load("contracts/PendleVaultFactory.vy")
        pa.update_blueprints(vault_blueprint, pendle_adapter_blueprint)
        pa.update_funds_allocator(funds_alloc)
        pa.update_governance(deployer)
        pa.update_pendle_contracts(
            PENDLE_ROUTER,
            PENDLE_ROUTER_STATIC,
            PENDLE_ORACLE
        )
    return pa


@pytest.fixture
def deployer(setup_chain):
    acc = boa.env.generate_address(alias="deployer")
    boa.env.set_balance(acc, 1000*10**18)
    return acc

@pytest.fixture
def trader(setup_chain):
    acc = boa.env.generate_address(alias="trader")
    boa.env.set_balance(acc, 1000*10**18)
    return acc

def _generic_erc20(trader, addr, slot):
    with open("contracts/vendor/IERC20.json") as f:
        j = json.load(f)
    factory = boa.loads_abi(json.dumps(j["abi"]), name="ERC20")
    st = factory.at(addr)
    #Trader needs to acquire some ETH, dunno how
    abi_encoded = eth_abi.encode(['address', 'uint256'], [trader, slot])
    storage_slot = Web3.solidity_keccak(["bytes"], ["0x" + abi_encoded.hex()])

    boa.env.set_storage(
        boa.util.abi.Address(addr).canonical_address,
        Web3.to_int(storage_slot),
        5000 * 10**18
    )
    print(st.balanceOf(trader))
    print(boa.env.get_balance(trader))
    assert st.balanceOf(trader) >= 5000 * 10**18, "Trader did not get 'airdrop'"
    return st


def probe_token_slot(trader, addr):
    with open("contracts/vendor/IERC20.json") as f:
        j = json.load(f)
    factory = boa.loads_abi(json.dumps(j["abi"]), name="ERC20")
    en = factory.at(addr)

    for x in range(0,500):
        # print(x)
        abi_encoded = eth_abi.encode(['address', 'uint256'], [trader, x])
        storage_slot = Web3.solidity_keccak(["bytes"], ["0x" + abi_encoded.hex()])
        boa.env.set_storage(
            boa.util.abi.Address(addr).canonical_address,
            Web3.to_int(storage_slot),
            5000 * 10**18
        )
        print(x, en.balanceOf(trader))
        if en.balanceOf(trader) >= 5000 * 10**18:
            return x

def _pendleOracle(pendleMarket, _PENDLE_ORACLE):
    with open("contracts/vendor/PendlePtLpOracle.json") as f:
        j = json.load(f)
    factory = boa.loads_abi(json.dumps(j["abi"]), name="PendlePtLpOracle")
    oracle = factory.at(_PENDLE_ORACLE)
    increaseCardinalityRequired, cardinalityRequired, oldestObservationSatisfied = oracle.getOracleState(pendleMarket, 1200)
    if increaseCardinalityRequired:
        pendleMarket.increaseObservationsCardinalityNext(cardinalityRequired)
        print("cardinality increased")
    #just in case, simulate passage of time
    boa.env.time_travel(seconds=1200)
    increaseCardinalityRequired, cardinalityRequired, oldestObservationSatisfied = oracle.getOracleState(pendleMarket, 1200)
    print(increaseCardinalityRequired, cardinalityRequired, oldestObservationSatisfied)
    assert increaseCardinalityRequired==False, "increaseCardinality failed"
    assert oldestObservationSatisfied==True, "oldestObservation is not Satisfied"
    return oracle

def pendle_Market(_pendle_market):
    with open("contracts/vendor/IPMarketV3.json") as f:
        j = json.load(f)
    factory = boa.loads_abi(json.dumps(j["abi"]), name="IPMarketV3")
    return factory.at(_pendle_market)

def _pendle_adapter(deployer, asset, _pendle_market):
    with boa.env.prank(deployer):
        pa = boa.load("contracts/adapters/PendleAdapter.vy", asset, PENDLE_ROUTER, PENDLE_ROUTER_STATIC, _pendle_market, PENDLE_ORACLE)
    return pa

@pytest.fixture
def funds_alloc(setup_chain, deployer):
    with boa.env.prank(deployer):
        f = boa.load("contracts/FundsAllocator.vy")
    return f



def pendle_pt(_pendle_pt):
    with open("contracts/vendor/IERC20.json") as f:
        j = json.load(f)
        factory = boa.loads_abi(json.dumps(j["abi"]), name="ERC20")
        return factory.at(_pendle_pt)

def pendle_SY(_sy):
    with open("contracts/vendor/IStandardizedYield.json") as f:
        j = json.load(f)
        factory = boa.loads_abi(json.dumps(j["abi"]), name="IStandardizedYield")
        return factory.at(_sy)


def market_test(_pendle_pt, asset, trader, deployer, _pendle_market, pendle_factory, _PENDLE_ORACLE, oracle, default_slippage=2.0):

    pt = pendle_pt(_pendle_pt)
    pendleMarket = pendle_Market(_pendle_market)
    pendleOracle = _pendleOracle(pendleMarket, _PENDLE_ORACLE)
    with boa.env.prank(trader):
        asset.transfer(deployer, 10**9)
    with boa.env.prank(deployer):
        asset.approve(pendle_factory, 10**9)
        pendle_factory.deploy_pendle_vault(
            asset,
            _pendle_market,
            "something blah",
            "psteth",
            18,
            Decimal(default_slippage),
            10**9
        )
    vault_addr_byte = pendle_factory._computation.output[12:]
    adaptervault = access_vault(vault_addr_byte)
    pendle_adapter = access_adapter(adaptervault.adapters(0))
    
    with boa.env.prank(trader):
        init_total_assets = adaptervault.totalAssets()
        asset.approve(adaptervault, 1*10**18)
        bal_pre = asset.balanceOf(trader)
        ex_rate = pendleOracle.getPtToAssetRate(_pendle_market, 1200)
        pregen_bytes = pendle_adapter.generate_pregen_info(10**18)
        adaptervault.deposit(1*10**18, trader, 0, [pregen_bytes])
        print("GAS USED FOR PENDLE DEPOSIT = ", adaptervault._computation.net_gas_used) 
        deducted = bal_pre - asset.balanceOf(trader)
        print(deducted)
        #rounding err...
        assert deducted == pytest.approx(1*10**18), "Invalid amount got deducted"
        print(pt.balanceOf(adaptervault))
        traderbal = adaptervault.balanceOf(trader)
        print(traderbal)
        trader_asset_bal = adaptervault.convertToAssets(traderbal)
        print(trader_asset_bal)
        total_assets = adaptervault.totalAssets()
        print(total_assets)
        #since trader is the first depositor, everything in the vault belongs to trader
        assert total_assets - init_total_assets == pytest.approx(trader_asset_bal), "Funds missing"
        #Ensure slippage is within limits (or else the vault would have reverted...)
        assert trader_asset_bal > deducted - (deducted * 0.02), "slipped beyond limits"
        assert adaptervault.claimable_yield_fees_available() == 0, "there should be no yield"

        #Move a month into future, to get yields
        #This should put us at around May 17th, and since pendle's TWAP accounts for interest, we should have yield
        boa.env.time_travel(seconds=60*60*24*30)
        traderbal = adaptervault.balanceOf(trader)
        trader_asset_bal_new = adaptervault.convertToAssets(traderbal)
        print(trader_asset_bal_new)
        assert trader_asset_bal_new > trader_asset_bal, "new trader balance should be higher because of yield"
        assert adaptervault.claimable_yield_fees_available() > 0, "there should be fees due to yield"
        #Lets withdraw 10% of traders funds...
        adaptervault.withdraw(trader_asset_bal_new // 10, trader, trader)
        print("GAS USED FOR PENDLE WITHDRAW = ", adaptervault._computation.net_gas_used) 
        assert (traderbal *9) //10 == pytest.approx(adaptervault.balanceOf(trader), rel=1e-2), "trader shares did not go down by 10%"

        #Get to  post maturity
        time_to_maturity = pendleMarket.expiry() - boa.env.evm.patch.timestamp
        assert time_to_maturity > 0, "maturity is not in future"
        boa.env.time_travel(seconds=time_to_maturity + 60)

        assert boa.env.evm.patch.timestamp > pendleMarket.expiry()
    with boa.env.prank(adaptervault.address):
        adapter_assets = pendle_adapter.totalAssets()
        adapter_pt = pt.balanceOf(adaptervault)
        print("adapter_assets: ", adapter_assets)
        print("adapter_pt: ", adapter_pt)
        assert adapter_assets==adapter_pt, "PT should be pegged to assets post-maturity"

    with boa.env.prank(trader):
        print(adaptervault.totalAssets())
        pt_bal_pre = pt.balanceOf(adaptervault)
        asset_bal_pre = asset.balanceOf(adaptervault)
        trader_bal_pre = asset.balanceOf(trader)
        assert adaptervault.balanceOf(trader) == pytest.approx(adaptervault.convertToShares( adaptervault.convertToAssets(adaptervault.balanceOf(trader))))

        adaptervault.withdraw(
            adaptervault.convertToAssets(adaptervault.balanceOf(trader)),
            trader,
            trader
        )
        pt_bal_post = pt.balanceOf(adaptervault)
        asset_bal_post = asset.balanceOf(adaptervault)
        trader_bal_post = asset.balanceOf(trader)
        #The total PT burned should equal total stETH gained by both trader and vault
        pt_burned = pt_bal_pre - pt_bal_post
        print("pt_burned: ", pt_burned)
        trader_asset_gained = trader_bal_post - trader_bal_pre
        print("trader_asset_gained: ", trader_asset_gained)
        vault_asset_gained = asset_bal_post - asset_bal_pre
        print("vault_asset_gained: ", vault_asset_gained)
        print("total gained: ", trader_asset_gained + vault_asset_gained)
        normalized_assets = oracle(trader_asset_gained + vault_asset_gained)
        print("normalized_assets: ", normalized_assets)
        #Theres always rounding issues somewhere...
        assert pt_burned == pytest.approx(normalized_assets), "withdraw was not pegged"

        #Lets try a deposit, it all should goto cash
        asset.approve(adaptervault, 1*10**18)
        adaptervault.deposit(1*10**18, trader)
        assert asset.balanceOf(adaptervault) - asset_bal_post == pytest.approx(10**18), "asset not gained sufficiently"
        assert pt.balanceOf(adaptervault) - pt_bal_post == 0, "managed to deposit to PT post-maturity"

def pegged_oracle(wrapped):
    return wrapped

def test_markets_ezeth(setup_chain, trader, deployer, pendle_factory):
    #stETH on mainnet
    PENDLE_MARKET="0x5E03C94Fc5Fb2E21882000A96Df0b63d2c4312e2" #Pendle: PT-stETH-26DEC24/SY-stETH Market Token
    EZETH="0x2416092f143378750bb29b79eD961ab195CcEea5"
    PENDLE_PT="0x8EA5040d423410f1fdc363379Af88e1DB5eA1C34"
    # print(probe_token_slot(trader, EZETH))
    # return
    ezeth = _generic_erc20(trader, EZETH, 51)
    orc = pendle_SY("0x0dE802e3D6Cc9145A150bBDc8da9F988a98c5202")
    def exchange(wrapped):
        rate = orc.exchangeRate()
        return (wrapped * rate) // 10**18

    market_test(PENDLE_PT, ezeth, trader, deployer, PENDLE_MARKET, pendle_factory, PENDLE_ORACLE, exchange)

def test_markets_rseth(setup_chain, trader, deployer, pendle_factory):
    #rsETH on mainnet
    PENDLE_MARKET="0x6Ae79089b2CF4be441480801bb741A531d94312b"
    RSETH="0x4186BFC76E2E237523CBC30FD220FE055156b41F"
    PENDLE_PT="0xAFD22F824D51Fb7EeD4778d303d4388AC644b026"
    # print(probe_token_slot(trader, RSETH))
    orc = pendle_SY("0xf176fB51F4eB826136a54FDc71C50fCd2202E272")
    def exchange(wrapped):
        rate = orc.exchangeRate()
        return (wrapped * rate) // 10**18
    rseth = _generic_erc20(trader, RSETH, 5)
    market_test(PENDLE_PT, rseth, trader, deployer, PENDLE_MARKET, pendle_factory, PENDLE_ORACLE, exchange)


def test_markets_eeth(setup_chain, trader, deployer, pendle_factory):
    #stETH on mainnet
    PENDLE_MARKET="0x952083cde7aaa11AB8449057F7de23A970AA8472" #Pendle: PT-stETH-26DEC24/SY-stETH Market Token
    EETH="0x35751007a407ca6FEFfE80b3cB397736D2cf4dbe"
    PENDLE_PT="0x1c27Ad8a19Ba026ADaBD615F6Bc77158130cfBE4"
    # print(probe_token_slot(trader, EETH))
    # return
    orc = pendle_SY("0xa6C895EB332E91c5b3D00B7baeEAae478cc502DA")
    def exchange(wrapped):
        rate = orc.exchangeRate()
        return (wrapped * rate) // 10**18

    eeth = _generic_erc20(trader, EETH, 51)
    market_test(PENDLE_PT, eeth, trader, deployer, PENDLE_MARKET, pendle_factory, PENDLE_ORACLE, exchange, default_slippage=4.0)

