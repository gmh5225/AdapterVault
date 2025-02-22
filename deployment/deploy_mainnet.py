import boa, os
from eth_account import Account

MULTISIG = "0x5287218b3E9B3b9D394e0A0656eD256fAfFd333a"
PENDLE_ROUTER="0x00000000005BBB0EF59571E58418F9a4357b68A0"
NOTHING="0x0000000000000000000000000000000000000000"
PENDLE_ROUTER_STATIC="0x263833d47eA3fA4a30f269323aba6a107f9eB14C"
PENDLE_ORACLE="0x66a1096C6366b2529274dF4f5D8247827fe4CEA8"


#---- contracts deployed ----
PENDLE_ADAPTER_BLUEPRINT    = "0x7D87e88aA7000fe8c2C3B450844A2dc3A2312919" #Update here if deployed
ADAPTERVAULT_BLUEPRINT      = "0x295d9c01b1A8904322198E97172604a38cac034e" #Update here if deployed
FUNDS_ALLOCATOR             = "0x1904163120C9345c1b41C520481CC677768E944d" #Update here if deployed
GOVERNANCE                  = "0xEdf4B1a86320a7b635F4a5E90044C928A16C781a" #Update here if deployed
PENDLE_FACTORY              = "0xcd3FF638DB6C1266b312B567DDE687C26A3314e5" #Update here if deployed
PT_MIGRATOR                 = "0x33376eE814558e305c6279C66117499757C6F92f"

#------ vaults -----------
VAULT_RSETH = "0xB8D5D36A40019f79b6B70a1932805476B2aCa6eF"
VAULT_RSWETH = "0x4521B903d65103Cd6265F898fE4ac3243884273f"
VAULT_EETH = "0xd1Ea80934222a21e330DAe9ad0354B4C139ae49F"
VAULT_EZETH = "0x1099ac45b80059733F719C7Dedf5a8ffCf02aAa8"
VAULT_USDE = "0xE0229dCFa4D84998484a27Ba01B4c2e78B1F02D3"
VAULT_SUSDE = "0x10Efb86d59eB8Ae3d4a7966B4ab9Ceb97e96D212"
VAULT_EETH_KARAK = "0x3af0B7d4691c4bCF2e3f9DAf8EA5A24960Fc30EB"
VAULT_USDE_KARAK = "0xA63B7542C546Ee2258010C44a5B94dbD80cA038f"
#---------------------------


if "__main__" in __name__:
    rpc = os.environ.get("RPC_URL")
    assert rpc is not None and rpc != "", "RPC_URL MUST BE PROVIDED!!!"
    boa.set_network_env(rpc)
    private_key = os.environ.get("PRIVATE_KEY")
    assert private_key is not None and private_key != "", "PRIVATE_KEY MUST BE PROVIDED!!!"
    boa.env.add_account(Account.from_key(private_key))
    gas_price=boa.env.get_gas_price()
    if PENDLE_ADAPTER_BLUEPRINT == "":
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 1534994 * gas_price/10**18, " ETH")
        input("Going to deploy PendleAdapter blueprint (ctrl+c to abort, enter to continue)")
        pa = boa.load_partial("contracts/adapters/PendleAdapter.vy")
        pa.deploy_as_blueprint() #1,534,994
        exit()
    else:
        print("ADAPTERVAULT_BLUEPRINT already exists: ", PENDLE_ADAPTER_BLUEPRINT)
    if ADAPTERVAULT_BLUEPRINT == "":
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 5343449 * gas_price/10**18, " ETH")
        input("Going to deploy AdapterVault blueprint (ctrl+c to abort, enter to continue)")
        pa = boa.load_partial("contracts/AdapterVault.vy")
        pa.deploy_as_blueprint() #5,343,449
        exit()
    else:
        print("ADAPTERVAULT_BLUEPRINT already exists: ", ADAPTERVAULT_BLUEPRINT)
    if FUNDS_ALLOCATOR == "":
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 713222 * gas_price/10**18, " ETH")
        input("Going to deploy FundsAllocator (ctrl+c to abort, enter to continue)")
        pa = boa.load("contracts/FundsAllocator.vy") #713222
        print(pa) 
        exit()
    else:
        print("FUNDS_ALLOCATOR already exists: ", GOVERNANCE)
    if GOVERNANCE == "":
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 2846735 * gas_price/10**18, " ETH")
        input("Going to deploy Governance (ctrl+c to abort, enter to continue)")
        pa = boa.load("contracts/Governance.vy", MULTISIG, 60*60*24*30) #2846735
        print(pa) 
        exit()
    else:
        print("GOVERNANCE already exists: ", GOVERNANCE)
    if PENDLE_FACTORY == "":
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 896928 * gas_price/10**18, " ETH")
        input("Going to deploy PendleVaultFactory (ctrl+c to abort, enter to continue)")
        pa = boa.load("contracts/PendleVaultFactory.vy") #896928
        print(pa) 
        exit()
    else:
        print("PENDLE_FACTORY already exists: ", PENDLE_FACTORY)
    if PT_MIGRATOR == "":
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 896928 * gas_price/10**18, " ETH")
        input("Going to deploy PTMigrationRouter (ctrl+c to abort, enter to continue)")
        pa = boa.load("contracts/PTMigrationRouter.vy", PENDLE_ROUTER) #896928
        print(pa) 
        exit()
    else:
        print("PT_MIGRATOR already exists: ", PT_MIGRATOR)
    #Ensure all values for factory are correct... bottom-up, change owner last
    factory = boa.load_partial("contracts/PendleVaultFactory.vy").at(PENDLE_FACTORY)
    if factory.pendle_router() != PENDLE_ROUTER or factory.pendle_router_static() != PENDLE_ROUTER_STATIC or factory.pendle_oracle() != PENDLE_ORACLE:
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 90807 * gas_price/10**18, " ETH")
        input("Going to deploy set pendle settings into factory (ctrl+c to abort, enter to continue)")
        factory.update_pendle_contracts(
            PENDLE_ROUTER,
            PENDLE_ROUTER_STATIC,
            PENDLE_ORACLE,
            gas = 150000
        ) #90807
    if factory.governance_impl() != GOVERNANCE:
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 45816 * gas_price/10**18, " ETH")
        input("Going to deploy set governance settings into factory (ctrl+c to abort, enter to continue)")
        factory.update_governance(GOVERNANCE, gas=100000) #45816
    if factory.funds_allocator_impl() != FUNDS_ALLOCATOR:
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 45816 * gas_price/10**18, " ETH")
        input("Going to deploy set fundsallocator settings into factory (ctrl+c to abort, enter to continue)")
        factory.update_funds_allocator(FUNDS_ALLOCATOR, gas=100000) #45816
    if factory.adapter_vault_blueprint() != ADAPTERVAULT_BLUEPRINT or factory.pendle_adapter_blueprint() != PENDLE_ADAPTER_BLUEPRINT:
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 68330 * gas_price/10**18, " ETH")
        input("Going to deploy set blueprint into factory (ctrl+c to abort, enter to continue)")
        factory.update_blueprints(ADAPTERVAULT_BLUEPRINT, PENDLE_ADAPTER_BLUEPRINT, gas=200000) #68330


    if factory.owner() != MULTISIG:
        print("estimated gas price is: ", gas_price/10**9, " gwei")
        print("estimated gas cost: ", 28269 * gas_price/10**18, " ETH")
        input("Going to change owner of factory (ctrl+c to abort, enter to continue)")
        factory.replace_owner(MULTISIG, gas=50000) #28269
