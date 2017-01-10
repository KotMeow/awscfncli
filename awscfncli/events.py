# -*- encoding: utf-8 -*-

__author__ = 'kotaimen'
__date__ = '04/01/2017'

"""Print stack events"""

import time
import click
import botocore.exceptions
import threading

STATUS_TO_COLOR = {
    'CREATE_IN_PROGRESS': dict(fg='yellow'),
    'CREATE_FAILED': dict(fg='red'),
    'CREATE_COMPLETE': dict(fg='green'),
    'ROLLBACK_IN_PROGRESS': dict(fg='yellow'),
    'ROLLBACK_FAILED': dict(fg='red'),
    'ROLLBACK_COMPLETE': dict(fg='green'),
    'DELETE_IN_PROGRESS': dict(fg='white', dim=True),
    'DELETE_FAILED': dict(fg='red'),
    'DELETE_SKIPPED': dict(fg='white', dim=True),
    'DELETE_COMPLETE': dict(fg='green'),
    'UPDATE_IN_PROGRESS': dict(fg='yellow'),
    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': dict(fg='green'),
    'UPDATE_COMPLETE': dict(fg='green'),
    'UPDATE_ROLLBACK_IN_PROGRESS': dict(fg='red'),
    'UPDATE_ROLLBACK_FAILED': dict(fg='red'),
    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': dict(fg='red'),
    'UPDATE_ROLLBACK_COMPLETE': dict(fg='green'),
    'UPDATE_FAILED': dict(fg='red'),
    'REVIEW_IN_PROGRESS': dict(fg='yellow', dim=True),
}


def tail_stack_events(stack,
                      latest_events=5,
                      event_limit=10000,
                      time_limit=3600,
                      check_interval=5):
    """Tail stack events and print them"""
    then = time.time()

    visited_events = set()
    first_run = True

    # loop until time limit
    while time.time() - then < time_limit:
        # or too many events are visited
        if len(visited_events) > event_limit:
            break

        # get all stack events, latest at latest_events
        try:
            events = list(stack.events.all())
        except botocore.exceptions.ClientError as e:
            click.echo(str(e))
            break
        else:
            events.reverse()
            event_count = len(events)

        for n, e in enumerate(events):
            # skip visited events
            if e.event_id in visited_events:
                continue
            else:
                visited_events.add(e.event_id)

            if first_run:
                if latest_events > 0:
                    if n < event_count - latest_events:
                        continue

            click.echo(e.timestamp.strftime('%x %X'), nl=False)
            click.echo(' - ', nl=False)
            click.echo(click.style(e.resource_status,
                                   **STATUS_TO_COLOR[e.resource_status]),
                       nl=False)
            click.echo(' - %s(%s)' % (e.logical_resource_id, e.resource_type),
                       nl=False)
            if e.resource_status_reason:
                click.echo(' - %s' % e.resource_status_reason)
            elif e.physical_resource_id:
                click.echo(' - %s' % e.physical_resource_id)
            else:
                click.echo('')

        else:
            first_run = False

        time.sleep(check_interval)


def start_tail_stack_events_daemon(stack,
                                   latest_events=5,
                                   event_limit=10000,
                                   time_limit=3600,
                                   check_interval=5):
    thread = threading.Thread(target=tail_stack_events,
                              args=(stack, latest_events, event_limit,
                                    time_limit, check_interval))
    thread.daemon = True
    thread.start()
