odoo.define("cnd_mail_activity_geolocation.KanbanActivity", function (require) {
    "use strict";

    require("mail.Activity");
    const field_registry = require('web.field_registry');

    const KanbanActivity = field_registry.get('kanban_activity');

    const ActivityCell = KanbanActivity.extend({
        _sendActivityFeedback: function (activityID, feedback, attachmentIds) {
            alert('_sendActivityFeedback FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF');
            return this._rpc({
                    model: 'mail.activity',
                    method: 'action_feedback',
                    args: [[activityID]],
                    kwargs: {
                        feedback: 'VALERIA: ' + feedback,
                        attachment_ids: attachmentIds || [],
                    },
                    context: this.record.getContext(),
                });
        },
    });

    return ActivityCell;

});

// odoo.define('cnd_mail_activity_geolocation.KanbanActivity', function (require) {
//         "use strict";
    
//     const BasicActivity = require('mail.BasicActivity');
    
//     require('mail.Activity');

//     var Activity = BasicActivity.extend({
//         _sendActivityFeedback: function (activityID, feedback, attachmentIds) {
//             alert('_sendActivityFeedback FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF');
//             return this._rpc({
//                     model: 'mail.activity',
//                     method: 'action_feedback',
//                     args: [[activityID]],
//                     kwargs: {
//                         feedback: 'VALERIA: ' + feedback,
//                         attachment_ids: attachmentIds || [],
//                     },
//                     context: this.record.getContext(),
//                 });
//         },
//     });
    
//     });