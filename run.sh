lttng create mytrace
lttng enable-event -u functrace:func_enter 
lttng enable-event -u functrace:func_exit
lttng add-context -u -t pthread_id
lttng add-context -u -t vpid
lttng add-context -u -t procname
lttng start mytrace
./app
lttng stop && lttng view 
lttng view > func.txt
lttng destroy mytrace


