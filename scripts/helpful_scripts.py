from os import link
from brownie import (
    network,
    config,
    accounts,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)

DECIMALS = 8
STARTING_PRICE = 4000 * 10 ** 8
LOCAL_DEV_ENVIRONMENTS = ["ganache-local", "development"]
FORKED_MAINNET_ENVIRONMENTS = ["mainnet-fork"]


def get_account(index=0, id=None):
    # if given an index use that from the randomly generated brownie accounts
    if index:
        return accounts[index]
    # if we pass an id, load that id from our accounts that we added to brownie -> `brownie accounts list`
    if id:
        return accounts.load(id)
    # if neither then check current active network
    ## if dev then return random first account
    if (
        network.show_active() in LOCAL_DEV_ENVIRONMENTS
        or network.show_active() in FORKED_MAINNET_ENVIRONMENTS
    ):
        return accounts[0]
    ## if not-dev then use account from .env
    return accounts.add(config["wallets"]["from_key"])


def deploy_mocks(decimals=DECIMALS, initial_value=STARTING_PRICE):
    account = get_account()
    print("Deploying mocks...")
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Mocks Deployed!")


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """This function will grab the contract addresses from the brownie config if defined,
    otherwise, it will deploy a mock version of that contract and return that mock contract.

        Args:
            contract_name (string)

        Returns:
            brownie.netork.contract.ProjectContract: The most recently deployed version of this contract.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_DEV_ENVIRONMENTS:
        print("Using Mocks...")
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[
            -1
        ]  # aka for eth_usd_price_feed == MockV3Aggregator[-1] <- latest contract
    else:
        print("Getting real contract from abi")
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            name=contract_type._name, address=contract_address, abi=contract_type.abi
        )
    return contract
    # contract_type.deploy({"from":get_account()})


def fund_with_link(
    contract_address, account=None, link_token=None, amount=10 ** 17
):  # 0.1 Link
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract("link_token")
    fund_ctr_txn = link_token.transfer(contract_address, amount, {"from": account})
    # link_token_contract = interface.LinkTokenInterface(
    #     link_token.address,
    # )
    # fund_ctr_txn = link_token_contract.transfer(
    #     contract_address, amount, {"from": account}
    # )
    fund_ctr_txn.wait(1)
    print("Funded contract!")
    return fund_ctr_txn
