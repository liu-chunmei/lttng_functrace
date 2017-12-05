lttng create mytrace
lttng enable-event –u functrace:func_enter functrace:func_exit
lttng start mytrace
./app
lttng stop && lttng view

