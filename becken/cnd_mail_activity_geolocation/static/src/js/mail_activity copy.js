odoo.define('hr_attendance_geolocation.Activity', function (require) {
    'use strict';
    const {
        registerInstancePatchModel,
        registerFieldPatchModel,
    } = require('mail/static/src/model/model_core.js');
    const { attr, one2one } = require('mail/static/src/model/model_field.js');
    registerInstancePatchModel('mail.activity', 'hr_attendance_geolocation.Activity', {
        async markAsDone({ attachments = [], feedback = false }) {
            const attachmentIds = attachments.map(attachment => attachment.id);
            // feedback = 'PEDRO: ' + feedback;
            await this.async(() => this.env.services.rpc({
                model: 'mail.activity',
                method: 'action_feedback',
                args: [[this.id]],
                kwargs: {
                    attachment_ids: attachmentIds,
                    feedback: feedback,
                    check_in_latitude: 13.13,
                    check_in_longitude: 88.88,
                },
            }));
            this.thread.refresh();
            location.reload();
            this.delete();
        }
    });
});


// odoo.define('hr_attendance_geolocation.Activity', function (require) {
//     "use strict";

//     var Activity = require('mail.Activity');

//     Activity.include({

//         /**
//          * @private
//          * @param {integer} activityID
//          * @param {string} feedback
//          * @param {integer[]} attachmentIds
//          * @return {Promise}
//          */
//         _sendActivityFeedback: function (activityID, feedback, attachmentIds) {
//             alert('_sendActivityFeedback');
//             feedback = 'HOLAS ' + feedback;
//             return self._super(activityID, feedback, attachmentIds);
//             // return this._rpc({
//             //     model: 'mail.activity',
//             //     method: 'action_feedback',
//             //     args: [[activityID]],
//             //     kwargs: {
//             //         feedback: feedback,
//             //         attachment_ids: attachmentIds || [],
//             //     },
//             //     context: this.record.getContext(),
//             // });
//         },

//         /**
//          * @param {Object} param0
//          * @param {mail.attachment[]} [param0.attachments=[]]
//          * @param {string|boolean} [param0.feedback=false]
//          */
//         async markAsDone({ attachments = [], feedback = false }) {
//             const attachmentIds = attachments.map(attachment => attachment.id);
//             feedback = 'DONDE ESTAN PERROS: ' + feedback;
//             await this.async(() => this.env.services.rpc({
//                 model: 'mail.activity',
//                 method: 'action_feedback',
//                 args: [[this.id]],
//                 kwargs: {
//                     attachment_ids: attachmentIds,
//                     feedback,
//                 },
//             }));
//             this.thread.refresh();
//             this.delete();
//         }
//     });

// });