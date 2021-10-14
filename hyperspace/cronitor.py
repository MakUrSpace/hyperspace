from hyperspace.bounty_system.bounty_up import process_ups


def lambda_handler(event, context):
    process_ups()
